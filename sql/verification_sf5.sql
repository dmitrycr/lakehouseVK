WITH expected AS
    (SELECT l.orderkey,
            SUM(l.extendedprice * (1 - l.discount)) AS revenue,
            o.orderdate,
            o.shippriority
     FROM lakehouse.bench_sf5_20261017_172546_parquet_zstd_r1.customer c
     JOIN lakehouse.bench_sf5_20261017_172546_parquet_zstd_r1.orders o ON c.custkey = o.custkey
     JOIN lakehouse.bench_sf5_20261017_172546_parquet_zstd_r1.lineitem l ON l.orderkey = o.orderkey
     WHERE c.mktsegment = 'BUILDING'
         AND o.orderdate < DATE '1995-03-15'
         AND l.shipdate > DATE '1995-03-15'
     GROUP BY l.orderkey,
              o.orderdate,
              o.shippriority
     ORDER BY revenue DESC,
              o.orderdate,
              l.orderkey
     LIMIT 10),
     a AS
    (SELECT orderkey,
            round(CAST(revenue AS DECIMAL(24, 4)), 2) revenue,
            orderdate,
            shippriority
     FROM expected),
     b AS
    (SELECT orderkey,
            round(CAST(revenue AS DECIMAL(24, 4)), 2) revenue,
            orderdate,
            shippriority
     FROM lakehouse.medallion_sf5_20261017_172546.q3_top_orders)
SELECT 'missing' AS difference,
       count(*) AS ROWS
FROM
    (SELECT *
     FROM a
     EXCEPT SELECT *
     FROM b)
UNION ALL
SELECT 'extra',
       count(*)
FROM
    (SELECT *
     FROM b
     EXCEPT SELECT *
     FROM a);
