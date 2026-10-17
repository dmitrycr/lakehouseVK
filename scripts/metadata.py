#!/usr/bin/env python3
from lab import ROOT, RUN, explain, guard, q3, query, save


def validate(t):
    cols, _ = query(f"SHOW COLUMNS FROM {t}")
    columns = ",".join(x["Column"] for x in cols)
    select = f"SELECT count(*) AS rows,sum(orderkey) AS keys,checksum(ROW({columns})) AS checksum,sum(CAST(extendedprice AS DECIMAL(20,2))) AS exact_price,sum(CAST(discount AS DECIMAL(4,2))) AS exact_discounts FROM "
    a, _ = query(select + t, "files_exact_after")
    b, _ = query(select + "lakehouse.bronze.lineitem", "files_exact_source")
    assert a == b, (a, b)
    save(
        "metadata_integrity",
        [dict(table=t, **a[0]), dict(table="lakehouse.bronze.lineitem", **b[0])],
    )


def main():
    t = f"lakehouse.benchmark.lineitem_files_{RUN}"
    statements = []
    for i in range(24):
        guard()
        s = (
            f"CREATE TABLE {t} WITH (format='PARQUET',compression_codec='ZSTD') AS "
            if i == 0
            else f"INSERT INTO {t} "
        ) + f"SELECT * FROM lakehouse.bronze.lineitem WHERE mod(orderkey / 32,24)={i}"
        statements.append(s)
        query(s, f"files_insert_{RUN}_{i}")
        print("INSERT", i, flush=True)

    def state(label):
        f, _ = query(
            f'SELECT count(*) AS files,sum(record_count) AS rows,sum(file_size_in_bytes) AS bytes FROM lakehouse.benchmark."lineitem_files_{RUN}$files"'
        )
        m, _ = query(
            f'SELECT count(*) AS manifests,sum(length) AS manifest_bytes FROM lakehouse.benchmark."lineitem_files_{RUN}$manifests"'
        )
        snap, _ = query(
            f'SELECT count(*) AS snapshots FROM lakehouse.benchmark."lineitem_files_{RUN}$snapshots"'
        )
        return dict(stage=label, table=t, **f[0], **m[0], **snap[0])

    states = [state("before")]
    assert int(states[0]["files"]) > 8, states
    reads = []
    q = q3("lakehouse.bronze").replace("lakehouse.bronze.lineitem", t)
    expected, _ = query(q3("tpch.sf1"))
    actual, _ = query(q)
    assert [x["orderkey"] for x in actual] == [x["orderkey"] for x in expected]
    for i in range(3):
        reads.append(dict(stage="before", repeat=i + 1, **explain(q, f"files_before_{RUN}_{i}")))
    s = f"ALTER TABLE {t} EXECUTE optimize_manifests"
    statements.append(s)
    query(s, f"manifests_optimize_{RUN}")
    states.append(state("manifests_optimized"))
    for i in range(3):
        reads.append(
            dict(
                stage="manifests_optimized",
                repeat=i + 1,
                **explain(q, f"manifests_after_{RUN}_{i}"),
            )
        )
    s = f"ALTER TABLE {t} EXECUTE optimize(file_size_threshold => '100MB')"
    statements.append(s)
    query(s, f"files_optimize_{RUN}")
    states.append(state("data_optimized"))
    for i in range(3):
        reads.append(
            dict(stage="data_optimized", repeat=i + 1, **explain(q, f"files_after_{RUN}_{i}"))
        )
    save("metadata_states", states)
    save("metadata_reads", reads)
    (ROOT / "sql/metadata_experiment.sql").write_text(";\n".join(statements) + ";\n")
    validate(t)
    print(states, flush=True)


if __name__ == "__main__":
    main()
