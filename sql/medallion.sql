-- Safe for an existing lakehouse: IF NOT EXISTS never overwrites existing tables.
-- Run verification afterwards: it catches an existing incompatible dataset.

CREATE SCHEMA IF NOT EXISTS lakehouse.bronze;

CREATE SCHEMA IF NOT EXISTS lakehouse.silver;

CREATE SCHEMA IF NOT EXISTS lakehouse.gold;

CREATE TABLE IF NOT EXISTS lakehouse.bronze.customer
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf1.customer;

CREATE TABLE IF NOT EXISTS lakehouse.bronze.orders
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf1.orders;

CREATE TABLE IF NOT EXISTS lakehouse.bronze.lineitem
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf1.lineitem;

CREATE TABLE IF NOT EXISTS lakehouse.silver.q3_order_lines
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT c.custkey,
       l.orderkey,
       l.linenumber,
       o.orderdate,
       o.shippriority,
       l.extendedprice,
       l.discount,
       l.extendedprice * (1 - l.discount) AS line_revenue
FROM lakehouse.bronze.customer c
JOIN lakehouse.bronze.orders o ON c.custkey = o.custkey
JOIN lakehouse.bronze.lineitem l ON l.orderkey = o.orderkey
WHERE c.mktsegment = 'BUILDING'
    AND o.orderdate < DATE '1995-03-15'
    AND l.shipdate > DATE '1995-03-15'
    AND l.extendedprice IS NOT NULL
    AND l.discount IS NOT NULL;

CREATE TABLE IF NOT EXISTS lakehouse.gold.q3_top_orders
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT orderkey,
       sum(line_revenue) revenue,
       orderdate,
       shippriority
FROM lakehouse.silver.q3_order_lines
GROUP BY orderkey,
         orderdate,
         shippriority
ORDER BY revenue DESC,
         orderdate,
         orderkey
LIMIT 10;
