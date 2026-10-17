#!/usr/bin/env python3
import json
import os
import subprocess

from lab import LOG, save

p = subprocess.run(
    [
        "docker",
        "compose",
        "run",
        "--rm",
        "--no-deps",
        "--entrypoint",
        "aws",
        "minio-init",
        "--endpoint-url",
        "http://minio:9000",
        "s3api",
        "list-objects-v2",
        "--bucket",
        "lakehouse",
        "--output",
        "json",
    ],
    capture_output=True,
    text=True,
    check=True,
)
objects = json.loads(p.stdout).get("Contents", [])
groups = {}
for o in objects:
    key = o["Key"]
    name = key.rsplit("/", 1)[-1]
    kind = (
        "metadata_json"
        if key.endswith(".metadata.json")
        else "manifest_list"
        if name.startswith("snap-") and key.endswith(".avro")
        else "manifest"
        if key.endswith(".avro")
        else "data_parquet"
        if key.endswith(".parquet")
        else "data_orc"
        if key.endswith(".orc")
        else "other"
    )
    group = groups.setdefault(kind, dict(kind=kind, objects=0, bytes=0))
    group["objects"] += 1
    group["bytes"] += o["Size"]
save("minio_objects", list(groups.values()))
(LOG / os.environ.get("LAB_STORAGE_LOG", "minio-object-summary.txt")).write_text(
    json.dumps(
        dict(
            scope="Entire lakehouse bucket; includes historical snapshots and all experiments",
            groups=groups,
        ),
        indent=2,
    )
)
print(groups)
