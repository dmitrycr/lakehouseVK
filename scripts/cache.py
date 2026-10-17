#!/usr/bin/env python3
"""Compare explicitly enabled/disabled Iceberg metadata cache. OS cache is untouched."""

import subprocess
import time

from lab import BASE, explain, q3, query, save

for attempt in range(30):
    p = subprocess.run(BASE + ["SELECT 1"], text=True, capture_output=True)
    if p.returncode == 0:
        break
    time.sleep(2)
else:
    raise RuntimeError("Trino not ready after bounded retries")
rows = []
for cat in ["cache_on", "cache_off"]:
    query(q3(cat + ".bronze"), "cache_warmup_" + cat)
for rep in range(1, 6):
    modes = ["cache_on", "cache_off"] if rep % 2 else ["cache_off", "cache_on"]
    for cat in modes:
        rows.append(
            dict(catalog=cat, repeat=rep, **explain(q3(cat + ".bronze"), f"cache_{cat}_{rep}"))
        )
        save("cache", rows)
print(rows, flush=True)
