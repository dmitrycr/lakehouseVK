-- Executed statements; names are unique to this run. Use new suffix to repeat.

CREATE TABLE lakehouse.silver.q3_schema_demo_20261017_165837 AS
SELECT *
FROM lakehouse.silver.q3_order_lines
ORDER BY orderkey,
         linenumber
LIMIT 100;

ALTER TABLE lakehouse.silver.q3_schema_demo_20261017_165837 ADD COLUMN source_system VARCHAR;

ALTER TABLE lakehouse.silver.q3_schema_demo_20261017_165837 RENAME COLUMN orderdate TO order_date;

INSERT INTO lakehouse.silver.q3_schema_demo_20261017_165837
SELECT custkey,
       orderkey,
       linenumber,
       order_date,
       shippriority,
       extendedprice,
       discount,
       line_revenue,
       'demo'
FROM lakehouse.silver.q3_schema_demo_20261017_165837
ORDER BY orderkey,
         linenumber
LIMIT 1;

CREATE TABLE lakehouse.silver.q3_schema_demo_20261017_165837_restored AS
SELECT *
FROM lakehouse.silver.q3_schema_demo_20261017_165837
FOR VERSION AS OF 3588371785330260403;

SELECT
    (SELECT count(*)
     FROM lakehouse.silver.q3_schema_demo_20261017_165837) AS current_rows,

    (SELECT count(*)
     FROM lakehouse.silver.q3_schema_demo_20261017_165837
     WHERE source_system IS NULL) AS old_nulls,

    (SELECT count(*)
     FROM lakehouse.silver.q3_schema_demo_20261017_165837
     FOR VERSION AS OF 3588371785330260403) AS historic_rows,

    (SELECT count(*)
     FROM lakehouse.silver.q3_schema_demo_20261017_165837_restored) AS restored_rows;
