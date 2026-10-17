-- Recovered executed statements from script and retained query logs. Use a new suffix to repeat.

CREATE TABLE lakehouse.benchmark.lineitem_files_20261017_170959
WITH (
    format = 'PARQUET',
    compression_codec = 'ZSTD'
) AS
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 0;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 1;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 2;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 3;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 4;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 5;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 6;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 7;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 8;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 9;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 10;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 11;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 12;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 13;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 14;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 15;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 16;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 17;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 18;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 19;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 20;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 21;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 22;

INSERT INTO lakehouse.benchmark.lineitem_files_20261017_170959
SELECT *
FROM lakehouse.bronze.lineitem
WHERE mod(orderkey / 32, 24) = 23;

ALTER TABLE lakehouse.benchmark.lineitem_files_20261017_170959 EXECUTE optimize_manifests;

ALTER TABLE lakehouse.benchmark.lineitem_files_20261017_170959 EXECUTE optimize(file_size_threshold => '100MB');
