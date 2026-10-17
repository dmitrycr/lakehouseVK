-- Executed benchmark statements. Existing names are preserved: rerun via scripts/benchmark.sh for a new suffix.

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_parquet_zstd_r1;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r1.customer
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r1.orders
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r1.lineitem
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_parquet_gzip_r1;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r1.customer
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r1.orders
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r1.lineitem
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_orc_zstd_r1;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r1.customer
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r1.orders
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r1.lineitem
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_orc_gzip_r1;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r1.customer
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r1.orders
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r1.lineitem
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_parquet_zstd_r2;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r2.customer
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r2.orders
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r2.lineitem
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_parquet_gzip_r2;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r2.customer
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r2.orders
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r2.lineitem
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_orc_zstd_r2;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r2.customer
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r2.orders
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r2.lineitem
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_orc_gzip_r2;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r2.customer
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r2.orders
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r2.lineitem
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_parquet_zstd_r3;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r3.customer
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r3.orders
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_zstd_r3.lineitem
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_parquet_gzip_r3;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r3.customer
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r3.orders
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_parquet_gzip_r3.lineitem
WITH (
    format = 'PARQUET',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_orc_zstd_r3;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r3.customer
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r3.orders
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_zstd_r3.lineitem
WITH (
    format = 'ORC',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM tpch.sf5.lineitem;

CREATE SCHEMA lakehouse.bench_sf5_20261017_172546_orc_gzip_r3;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r3.customer
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.customer;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r3.orders
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.orders;

CREATE TABLE lakehouse.bench_sf5_20261017_172546_orc_gzip_r3.lineitem
WITH (
    format = 'ORC',
    compression_codec = 'GZIP'
) AS
SELECT *
FROM tpch.sf5.lineitem;
