#!/usr/bin/env python3
"""Non-destructive laboratory runner. Each experiment uses a new namespace."""

import csv
import datetime
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
RUN = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
LOG = ROOT / "evidence/logs"
LOG.mkdir(parents=True, exist_ok=True)
RESULT = (ROOT / os.environ.get("LAB_RESULTS_DIR", "results")).resolve()
if ROOT not in RESULT.parents:
    raise ValueError("LAB_RESULTS_DIR must be inside the project")
RESULT.mkdir(parents=True, exist_ok=True)
BASE = [
    "docker",
    "compose",
    "exec",
    "-T",
    "trino",
    "trino",
    "--no-progress",
    "--output-format",
    "CSV_HEADER",
    "--execute",
]


def query(sql, label=None):
    start = time.monotonic()
    p = subprocess.run(BASE + [sql], text=True, capture_output=True)
    elapsed = time.monotonic() - start
    if label:
        (LOG / (label + ".txt")).write_text(sql + ";\n\n" + p.stdout + p.stderr)
    if p.returncode:
        raise RuntimeError(p.stderr + p.stdout)
    return list(csv.DictReader(io.StringIO(p.stdout))), elapsed


def save(name, rows):
    if not rows:
        return
    with (RESULT / (name + ".csv")).open("w") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def guard(expected_bytes=0):
    free = shutil.disk_usage(ROOT).free
    if free < 22 * 1024**3 + expected_bytes:
        raise RuntimeError(
            f"Disk reserve: need 22 GiB plus {expected_bytes} projected bytes; free={free}; stopping writes"
        )


def q3(schema):
    return (
        (ROOT / "sql/q3_reference.sql")
        .read_text()
        .replace("tpch.sf1.", schema + ".")
        .strip()
        .rstrip(";")
    )


def verify():
    rows = []
    for layer, table in [
        ("bronze", "customer"),
        ("bronze", "orders"),
        ("bronze", "lineitem"),
        ("silver", "q3_order_lines"),
        ("gold", "q3_top_orders"),
    ]:
        t = f"lakehouse.{layer}.{table}"
        r, _ = query(f"SELECT count(*) AS rows FROM {t}", f"verify_{layer}_{table}")
        m, _ = query(
            f'SELECT count(*) AS files,sum(file_size_in_bytes) AS bytes FROM lakehouse.{layer}."{table}$files"'
        )
        query("SHOW CREATE TABLE " + t, f"ddl_{layer}_{table}")
        rows.append(
            dict(
                layer=layer,
                table=table,
                rows=r[0]["rows"],
                files=m[0]["files"],
                bytes=m[0]["bytes"],
                mib=int(m[0]["bytes"]) / 1048576,
            )
        )
    save("layers", rows)
    assert [int(x["rows"]) for x in rows] == [150000, 1500000, 6001215, 30519, 10], rows
    check = f"""WITH expected AS ({q3("tpch.sf1")}), a AS (
SELECT orderkey,round(revenue,2) revenue,orderdate,shippriority FROM expected), b AS (
SELECT orderkey,round(revenue,2) revenue,orderdate,shippriority FROM lakehouse.gold.q3_top_orders)
SELECT 'missing' AS difference,count(*) AS rows FROM (SELECT * FROM a EXCEPT SELECT * FROM b)
UNION ALL SELECT 'extra',count(*) FROM (SELECT * FROM b EXCEPT SELECT * FROM a)"""
    (ROOT / "sql/verification.sql").write_text(check + ";\n")
    r, _ = query(check, "gold_comparison")
    save("gold_comparison", r)
    assert all(int(x["rows"]) == 0 for x in r), r
    r, _ = query("SELECT * FROM lakehouse.gold.q3_top_orders ORDER BY revenue DESC", "gold")
    save("gold", r)
    r, _ = query(
        "SELECT count(*) AS rows,count(DISTINCT orderkey) AS orders,sum(line_revenue) AS revenue,count_if(extendedprice IS NULL OR discount IS NULL) AS nulls FROM lakehouse.silver.q3_order_lines",
        "silver_quality",
    )
    save("silver_quality", r)
    assert r[0]["rows"] == "30519" and r[0]["orders"] == "11620" and r[0]["nulls"] == "0"
    assert round(float(r[0]["revenue"]), 2) == 1115271243.51
    r, _ = query(
        "SELECT count(*) AS duplicate_keys FROM (SELECT orderkey,linenumber FROM lakehouse.silver.q3_order_lines GROUP BY 1,2 HAVING count(*)>1)",
        "silver_duplicates",
    )
    save("silver_duplicates", r)
    assert r[0]["duplicate_keys"] == "0"
    exists, _ = query(
        "SELECT count(*) AS n FROM lakehouse.information_schema.tables WHERE table_schema='benchmark' AND table_name='schema_demo'"
    )
    if exists[0]["n"] == "1":
        snapshots, _ = query('SELECT snapshot_id FROM lakehouse.benchmark."schema_demo$snapshots"')
        if any(x["snapshot_id"] == "3054311289263189975" for x in snapshots):
            r, _ = query(
                "SELECT (SELECT count(*) FROM lakehouse.benchmark.schema_demo) AS current_rows,(SELECT count(*) FROM lakehouse.benchmark.schema_demo FOR VERSION AS OF 3054311289263189975) AS historic_rows",
                "existing_time_travel",
            )
            save("existing_time_travel", r)


def evolution():
    guard()
    t = f"lakehouse.silver.q3_schema_demo_{RUN}"
    statements = [
        f"CREATE TABLE {t} AS SELECT * FROM lakehouse.silver.q3_order_lines ORDER BY orderkey,linenumber LIMIT 100"
    ]
    query(statements[0], "evolution_create_" + RUN)
    r, _ = query(
        f'SELECT snapshot_id FROM lakehouse.silver."q3_schema_demo_{RUN}$snapshots" ORDER BY committed_at LIMIT 1'
    )
    sid = r[0]["snapshot_id"]
    statements += [
        f"ALTER TABLE {t} ADD COLUMN source_system VARCHAR",
        f"ALTER TABLE {t} RENAME COLUMN orderdate TO order_date",
        f"INSERT INTO {t} SELECT custkey,orderkey,linenumber,order_date,shippriority,extendedprice,discount,line_revenue,'demo' FROM {t} ORDER BY orderkey,linenumber LIMIT 1",
        f"CREATE TABLE {t}_restored AS SELECT * FROM {t} FOR VERSION AS OF {sid}",
    ]
    for i, s in enumerate(statements[1:]):
        query(s, f"evolution_{RUN}_{i}")
    check = f"SELECT (SELECT count(*) FROM {t}) AS current_rows,(SELECT count(*) FROM {t} WHERE source_system IS NULL) AS old_nulls,(SELECT count(*) FROM {t} FOR VERSION AS OF {sid}) AS historic_rows,(SELECT count(*) FROM {t}_restored) AS restored_rows"
    r, _ = query(check, "evolution_result_" + RUN)
    save("evolution", r)
    assert r[0] == dict(
        current_rows="101", old_nulls="100", historic_rows="100", restored_rows="100"
    )
    query(f"SHOW COLUMNS FROM {t}", "evolution_columns_" + RUN)
    r, _ = query(
        f"SELECT count(*) AS differences FROM ((SELECT * FROM {t} FOR VERSION AS OF {sid} EXCEPT SELECT * FROM {t}_restored) UNION ALL (SELECT * FROM {t}_restored EXCEPT SELECT * FROM {t} FOR VERSION AS OF {sid}))",
        "restored_comparison",
    )
    assert r[0]["differences"] == "0"
    (ROOT / "sql/schema_evolution_time_travel.sql").write_text(
        "-- Executed statements; names are unique to this run. Use new suffix to repeat.\n"
        + ";\n".join(statements + [check])
        + ";\n"
    )


def explain(sql, label):
    rows, wall = query("EXPLAIN ANALYZE " + sql, label)
    plan = "\n".join(str(v) for r in rows for v in r.values())

    def ms(name):
        m = re.search(name + r"\s*[:=]\s*([\d.]+)(ns|us|ms|s|m)", plan)
        return (
            float(m[1]) * {"ns": 1e-6, "us": 0.001, "ms": 1, "s": 1000, "m": 60000}[m[2]]
            if m
            else ""
        )

    return dict(
        log_file="evidence/logs/" + label + ".txt",
        wall_s=wall,
        analysis_ms=ms("Analysis"),
        planning_ms=ms("Planning"),
        execution_ms=ms("Execution"),
        first_fragment_cpu_ms=ms("CPU"),
        physical_input=";".join(re.findall(r"Physical input: ([^\n]+)", plan)),
        splits=";".join(re.findall(r"Splits: ([^\n]+)", plan)),
    )


def benchmark():
    scale = int(os.environ.get("LAB_SCALE", "1"))
    if scale < 1:
        raise ValueError("LAB_SCALE must be a positive integer")
    archive = RESULT / ("archive_before_" + RUN)
    for name in ["writes", "reads", "checksums", "benchmark_summary", "run"]:
        source = RESULT / (name + (".json" if name == "run" else ".csv"))
        if source.exists():
            archive.mkdir(exist_ok=True)
            shutil.copy2(source, archive / source.name)
    guard(int(240e6 * scale * 12 * 1.15))
    configs = [("PARQUET", "ZSTD"), ("PARQUET", "GZIP"), ("ORC", "ZSTD"), ("ORC", "GZIP")]
    writes = []
    reads = []
    schemas = []
    aggregates = []
    statements = []
    expected, _ = query(q3(f"tpch.sf{scale}"), f"reference_sf{scale}_{RUN}")
    save("reference_q3", expected)

    def checkpoint(status):
        (RESULT / "run.json").write_text(
            json.dumps(dict(run_id=RUN, scale=scale, status=status, schemas=schemas), indent=2)
        )

    checkpoint("running")
    for rep in range(1, 4):
        for fmt, codec in configs:
            guard(int(265e6 * scale * 1.5))
            schema = f"lakehouse.bench_sf{scale}_{RUN}_{fmt.lower()}_{codec.lower()}_r{rep}"
            query(f"CREATE SCHEMA {schema}")
            schemas.append((schema, fmt, codec, rep))
            checkpoint("running")
            statements.append(f"CREATE SCHEMA {schema}")
            for table in ["customer", "orders", "lineitem"]:
                guard(
                    int({"customer": 10e6, "orders": 45e6, "lineitem": 210e6}[table] * scale * 1.5)
                )
                sql = f"CREATE TABLE {schema}.{table} WITH (format='{fmt}',compression_codec='{codec}') AS SELECT * FROM tpch.sf{scale}.{table}"
                print(f"WRITE sf{scale} {fmt}/{codec} repeat={rep} {table}", flush=True)
                _, wall = query(sql, f"write_{schema}_{table}")
                statements.append(sql)
                (RESULT / "executed.sql").write_text(";\n".join(statements) + ";\n")
                m, _ = query(
                    f'SELECT count(*) AS files,sum(record_count) AS rows,sum(file_size_in_bytes) AS bytes FROM {schema}."{table}$files"'
                )
                writes.append(
                    dict(
                        schema=schema,
                        format=fmt,
                        codec=codec,
                        replicate=rep,
                        table=table,
                        log_file=f"evidence/logs/write_{schema}_{table}.txt",
                        wall_s=wall,
                        **m[0],
                    )
                )
                save("writes", writes)
                key = {"customer": "custkey", "orders": "orderkey", "lineitem": "orderkey"}[table]
                cols, _ = query(f"SHOW COLUMNS FROM {schema}.{table}")
                columns = ",".join("t." + x["Column"] for x in cols)
                a, _ = query(
                    f"SELECT count(*) AS rows,sum({key}) AS key_sum,checksum(ROW({columns})) AS checksum FROM {schema}.{table} t",
                    f"checksum_{schema}_{table}",
                )
                aggregates.append(dict(schema=schema, table=table, **a[0]))
                save("checksums", aggregates)
            r, _ = query(q3(schema), f"q3_{schema}")
            save(f"q3_{fmt.lower()}_{codec.lower()}_r{rep}", r)
            assert [
                (x["orderkey"], round(float(x["revenue"]), 2), x["orderdate"], x["shippriority"])
                for x in r
            ] == [
                (x["orderkey"], round(float(x["revenue"]), 2), x["orderdate"], x["shippriority"])
                for x in expected
            ]
    # Balanced rotation of all formats; read one independent realization per format.
    first = schemas[:4]
    for repeat in range(1, 6):
        ordered = first[(repeat - 1) % 4 :] + first[: (repeat - 1) % 4]
        for schema, fmt, codec, rep in ordered:
            print(f"READ sf{scale} {fmt}/{codec} repeat={repeat}", flush=True)
            reads.append(
                dict(
                    schema=schema,
                    format=fmt,
                    codec=codec,
                    repeat=repeat,
                    **explain(q3(schema), f"read_{schema}_{repeat}"),
                )
            )
            save("reads", reads)
    for table in ["customer", "orders", "lineitem"]:
        values = {
            (a["rows"], a["key_sum"], a["checksum"]) for a in aggregates if a["table"] == table
        }
        assert len(values) == 1, values
    summary = []
    for fmt, codec in configs:
        w = [x for x in writes if x["format"] == fmt and x["codec"] == codec]
        totals = [sum(x["wall_s"] for x in w if x["replicate"] == r) for r in range(1, 4)]
        rr = [float(x["execution_ms"]) for x in reads if x["format"] == fmt and x["codec"] == codec]
        summary.append(
            dict(
                format=fmt,
                codec=codec,
                write_mean_s=statistics.mean(totals),
                write_min_s=min(totals),
                write_max_s=max(totals),
                bytes_mean=sum(int(x["bytes"]) for x in w) / 3,
                execution_mean_ms=statistics.mean(rr),
                execution_median_ms=statistics.median(rr),
                execution_stdev_ms=statistics.stdev(rr),
                execution_min_ms=min(rr),
                execution_max_ms=max(rr),
            )
        )
    save("benchmark_summary", summary)
    checkpoint("complete")


if __name__ == "__main__":
    for action in sys.argv[1:] or ["verify"]:
        print("START", action, RUN, flush=True)
        globals()[action]()
        print("DONE", action, flush=True)
