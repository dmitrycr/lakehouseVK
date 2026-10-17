#!/usr/bin/env python3
"""Validate an isolated benchmark directory and build Silver/Gold for that scale."""

import csv
import json
import re
import shutil
import statistics
from decimal import ROUND_HALF_UP, Decimal

from lab import LOG, RESULT, ROOT, guard, q3, query, save


def load_csv(name):
    with (RESULT / (name + ".csv")).open() as f:
        return list(csv.DictReader(f))


def main():
    run = json.loads((RESULT / "run.json").read_text())
    scale = int(run["scale"])
    sid = run["run_id"]
    assert run["status"] == "complete"
    (ROOT / "sql" / f"q3_reference_sf{scale}.sql").write_text(q3(f"tpch.sf{scale}") + ";\n")
    (ROOT / "sql" / f"benchmark_sf{scale}.sql").write_text(
        "-- Executed benchmark statements. Existing names are preserved: rerun via scripts/benchmark.sh for a new suffix.\n"
        + (RESULT / "executed.sql").read_text()
    )
    writes = load_csv("writes")
    reads = load_csv("reads")
    checks = load_csv("checksums")
    reference = load_csv("reference_q3")
    assert len(writes) == 36 and len(reads) == 20 and len(checks) == 36
    for table in ["customer", "orders", "lineitem"]:
        values = {(x["rows"], x["key_sum"], x["checksum"]) for x in checks if x["table"] == table}
        assert len(values) == 1, (table, values)

    def normalized(rows):
        return sorted(
            (
                int(x["orderkey"]),
                str(
                    Decimal(x["revenue"])
                    .quantize(Decimal("0.0001"))
                    .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ),
                x["orderdate"],
                int(x["shippriority"]),
            )
            for x in rows
        )

    for fmt, codec in [("parquet", "zstd"), ("parquet", "gzip"), ("orc", "zstd"), ("orc", "gzip")]:
        for rep in range(1, 4):
            assert normalized(load_csv(f"q3_{fmt}_{codec}_r{rep}")) == normalized(reference)
    for row in reads:
        plan = (ROOT / row["log_file"]).read_text()
        fragments = re.findall(r"\nFragment[^\n]*\n    CPU: ([\d.]+)(ns|us|ms|s|m)", plan)
        row["cpu_total_ms"] = sum(
            float(v) * {"ns": 1e-6, "us": 0.001, "ms": 1, "s": 1000, "m": 60000}[unit]
            for v, unit in fragments
        )
        row["scan_splits_total"] = sum(int(v) for v in re.findall(r"Splits: (\d+)", plan))
        assert float(row["execution_ms"]) > 0
    save("reads", reads)
    summary = load_csv("benchmark_summary")
    for row in summary:
        subset = [x for x in reads if x["format"] == row["format"] and x["codec"] == row["codec"]]
        row["planning_mean_ms"] = statistics.mean(float(x["planning_ms"]) for x in subset)
        row["cpu_total_mean_ms"] = statistics.mean(float(x["cpu_total_ms"]) for x in subset)
        row["scan_splits_mean"] = statistics.mean(float(x["scan_splits_total"]) for x in subset)
    save("benchmark_summary", summary)
    bronze = run["schemas"][0][0]
    schema = f"lakehouse.medallion_sf{scale}_{sid}"
    statements = [
        f"CREATE SCHEMA IF NOT EXISTS {schema}",
        f"""CREATE TABLE IF NOT EXISTS {schema}.q3_order_lines WITH (format='PARQUET',compression_codec='ZSTD') AS
SELECT c.custkey,l.orderkey,l.linenumber,o.orderdate,o.shippriority,l.extendedprice,l.discount,l.extendedprice*(1-l.discount) AS line_revenue
FROM {bronze}.customer c JOIN {bronze}.orders o ON c.custkey=o.custkey JOIN {bronze}.lineitem l ON l.orderkey=o.orderkey
WHERE c.mktsegment='BUILDING' AND o.orderdate<DATE '1995-03-15' AND l.shipdate>DATE '1995-03-15'
AND l.extendedprice IS NOT NULL AND l.discount IS NOT NULL""",
        f"""CREATE TABLE IF NOT EXISTS {schema}.q3_top_orders WITH (format='PARQUET',compression_codec='ZSTD') AS
SELECT orderkey,sum(line_revenue) revenue,orderdate,shippriority FROM {schema}.q3_order_lines
GROUP BY orderkey,orderdate,shippriority ORDER BY revenue DESC,orderdate,orderkey LIMIT 10""",
    ]
    (ROOT / "sql" / f"medallion_sf{scale}.sql").write_text(
        "-- Bronze sources are the first PARQUET/ZSTD benchmark realization; existing data is retained.\n"
        + ";\n".join(statements)
        + ";\n"
    )
    for i, sql in enumerate(statements):
        guard(100 * 1024**2)
        query(sql, f"sf{scale}_medallion_{sid}_{i}")
    gold, _ = query(
        f"SELECT * FROM {schema}.q3_top_orders ORDER BY revenue DESC", f"sf{scale}_gold_{sid}"
    )
    save("gold", gold)
    assert normalized(gold) == normalized(reference)
    check = f"""WITH expected AS ({q3(bronze)}), a AS (SELECT orderkey,round(CAST(revenue AS DECIMAL(24,4)),2) revenue,orderdate,shippriority FROM expected), b AS (SELECT orderkey,round(CAST(revenue AS DECIMAL(24,4)),2) revenue,orderdate,shippriority FROM {schema}.q3_top_orders)
SELECT 'missing' AS difference,count(*) AS rows FROM (SELECT * FROM a EXCEPT SELECT * FROM b)
UNION ALL SELECT 'extra',count(*) FROM (SELECT * FROM b EXCEPT SELECT * FROM a)"""
    (ROOT / "sql" / f"verification_sf{scale}.sql").write_text(check + ";\n")
    r, _ = query(check, f"sf{scale}_gold_comparison_{sid}")
    save("gold_comparison", r)
    assert all(x["rows"] == "0" for x in r)
    quality, _ = query(
        f"SELECT count(*) AS rows,count(DISTINCT orderkey) AS orders,sum(CAST(line_revenue AS DECIMAL(24,6))) AS revenue,count_if(extendedprice IS NULL OR discount IS NULL) AS nulls FROM {schema}.q3_order_lines",
        f"sf{scale}_quality_{sid}",
    )
    save("silver_quality", quality)
    assert quality[0]["nulls"] == "0"
    duplicates, _ = query(
        f"SELECT count(*) AS duplicate_keys FROM (SELECT orderkey,linenumber FROM {schema}.q3_order_lines GROUP BY 1,2 HAVING count(*)>1)",
        f"sf{scale}_duplicates_{sid}",
    )
    assert duplicates[0]["duplicate_keys"] == "0"
    save("silver_duplicates", duplicates)
    layers = []
    for layer, table, source in [
        ("bronze", t, bronze) for t in ["customer", "orders", "lineitem"]
    ] + [("silver", "q3_order_lines", schema), ("gold", "q3_top_orders", schema)]:
        counts, _ = query(f"SELECT count(*) AS rows FROM {source}.{table}")
        size, _ = query(
            f'SELECT count(*) AS files,sum(file_size_in_bytes) AS bytes FROM {source}."{table}$files"'
        )
        query(f"SHOW CREATE TABLE {source}.{table}", f"sf{scale}_ddl_{layer}_{table}_{sid}")
        layers.append(
            dict(
                layer=layer,
                table=f"{source}.{table}",
                rows=counts[0]["rows"],
                files=size[0]["files"],
                bytes=size[0]["bytes"],
                mib=int(size[0]["bytes"]) / 1048576,
            )
        )
    save("layers", layers)
    registry, _ = query(
        f"SELECT table_schema,table_name FROM lakehouse.information_schema.tables WHERE table_schema LIKE '%{sid}%' ORDER BY 1,2",
        f"sf{scale}_registry_{sid}",
    )
    save("experimental_tables", registry)
    run["medallion_schema"] = schema
    run["verified"] = True
    run["free_bytes_after"] = shutil.disk_usage(ROOT).free
    (RESULT / "run.json").write_text(json.dumps(run, indent=2))
    (LOG / f"sf{scale}_final_verification_{sid}.txt").write_text(
        json.dumps(
            dict(
                status="PASS",
                scale=scale,
                independent_writes=36,
                q3_timed_reads=20,
                all_12_q3_match_reference=True,
                all_checksums_match=True,
                medallion_schema=schema,
                gold_difference_rows=0,
                quality=quality[0],
                free_bytes=run["free_bytes_after"],
            ),
            indent=2,
        )
    )
    (ROOT / "results/scaled_run.json").write_text(
        json.dumps(dict(path=str(RESULT.relative_to(ROOT)), scale=scale, run_id=sid), indent=2)
    )
    print("PASS", json.dumps(run), flush=True)


if __name__ == "__main__":
    main()
