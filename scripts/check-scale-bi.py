#!/usr/bin/env python3
"""Check the new scale through Superset's authenticated SQL Lab API."""

import json
import subprocess

from lab import LOG, RESULT, save

run = json.loads((RESULT / "run.json").read_text())
assert run.get("verified")
bronze = run["schemas"][0][0]
gold = run["medallion_schema"]
scale = run["scale"]
code = r"""
import json
import os

import requests

s = requests.Session()
base = "http://localhost:8088"
r = s.post(
    base + "/api/v1/security/login",
    json=dict(
        username="admin",
        password=os.environ["SUPERSET_ADMIN_PASSWORD"],
        provider="db",
        refresh=True,
    ),
)
r.raise_for_status()
s.headers["Authorization"] = "Bearer " + r.json()["access_token"]
r = s.get(base + "/api/v1/security/csrf_token/")
r.raise_for_status()
s.headers["X-CSRFToken"] = r.json()["result"]
s.headers["Referer"] = base + "/"
r = s.get(base + "/api/v1/database/")
r.raise_for_status()
database = next(x for x in r.json()["result"] if x["database_name"] == "Lakehouse Trino")
for kind, sql in [
    (
        "bronze",
        f"SELECT mktsegment,count(*) customer_count FROM {os.environ['LAB_BRONZE_SCHEMA']}.customer GROUP BY mktsegment ORDER BY customer_count DESC",
    ),
    ("gold", f"SELECT * FROM {os.environ['LAB_GOLD_SCHEMA']}.q3_top_orders ORDER BY revenue DESC"),
]:
    r = s.post(
        base + "/api/v1/sqllab/execute/",
        json=dict(database_id=database["id"], sql=sql, runAsync=False, json=True, queryLimit=100),
    )
    r.raise_for_status()
    data = r.json()
    assert data["status"] == "success", data
    print(
        "SCALE_BI " + json.dumps(dict(kind=kind, sql=sql, data=data["data"], status=data["status"]))
    )
"""
command = [
    "docker",
    "compose",
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.superset.yml",
    "exec",
    "-T",
    "-e",
    f"LAB_BRONZE_SCHEMA={bronze}",
    "-e",
    f"LAB_GOLD_SCHEMA={gold}",
    "superset",
    "python",
    "-",
]
p = subprocess.run(command, input=code, text=True, capture_output=True)
(LOG / f"superset-sf{scale}-api.txt").write_text(p.stdout + p.stderr)
if p.returncode:
    raise RuntimeError(p.stderr + p.stdout)
records = [
    json.loads(line.removeprefix("SCALE_BI "))
    for line in p.stdout.splitlines()
    if line.startswith("SCALE_BI ")
]
assert len(records) == 2
for r in records:
    save("superset_" + r["kind"], r["data"])
    if r["kind"] == "bronze":
        assert sum(x["customer_count"] for x in r["data"]) == 150000 * scale
    if r["kind"] == "gold":
        assert len(r["data"]) == 10
print("PASS: Superset SQL Lab read Bronze and Gold at sf" + str(scale))
