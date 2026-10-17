"""Run inside Superset container. No credentials or access tokens are printed."""

import json
import os

import requests
from superset.app import create_app

from superset import db

app = create_app()
with app.app_context():
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.core import Database
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice

    database = db.session.query(Database).filter_by(database_name="Lakehouse Trino").one_or_none()
    if database is None:
        database = Database(
            database_name="Lakehouse Trino",
            sqlalchemy_uri="trino://superset@trino:8080/lakehouse/bronze",
            expose_in_sqllab=True,
            allow_run_async=False,
        )
        db.session.add(database)
        db.session.commit()
    dataset = (
        db.session.query(SqlaTable)
        .filter_by(database_id=database.id, schema="gold", table_name="q3_top_orders")
        .one_or_none()
    )
    if dataset is None:
        dataset = SqlaTable(database_id=database.id, schema="gold", table_name="q3_top_orders")
        db.session.add(dataset)
        db.session.commit()
        dataset.fetch_metadata()
        db.session.commit()
    chart = db.session.query(Slice).filter_by(slice_name="Q3: Top 10 orders").one_or_none()
    params = dict(
        viz_type="echarts_timeseries_bar",
        datasource=f"{dataset.id}__table",
        x_axis="orderkey",
        metrics=[
            dict(
                expressionType="SQL",
                sqlExpression="SUM(revenue)",
                label="Revenue",
                optionName="metric_revenue",
            )
        ],
        groupby=[],
        row_limit=10,
        order_desc=True,
        orientation="horizontal",
        rich_tooltip=True,
        show_legend=False,
        x_axis_sort="Revenue",
        x_axis_sort_asc=False,
    )
    if chart is None:
        chart = Slice(
            slice_name="Q3: Top 10 orders",
            viz_type="echarts_timeseries_bar",
            datasource_id=dataset.id,
            datasource_type="table",
            params=json.dumps(params),
        )
        db.session.add(chart)
        db.session.commit()
    dashboard = db.session.query(Dashboard).filter_by(slug="lakehouse-q3").one_or_none()
    if dashboard is None:
        dashboard = Dashboard(
            dashboard_title="Lakehouse — TPC-H Q3", slug="lakehouse-q3", published=True
        )
        dashboard.slices = [chart]
        dashboard.position_json = json.dumps(
            {
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
                "GRID_ID": {
                    "id": "GRID_ID",
                    "type": "GRID",
                    "children": ["ROW-1"],
                    "parents": ["ROOT_ID"],
                },
                "ROW-1": {
                    "id": "ROW-1",
                    "type": "ROW",
                    "children": ["CHART-1"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "CHART-1": {
                    "id": "CHART-1",
                    "type": "CHART",
                    "children": [],
                    "parents": ["ROOT_ID", "GRID_ID", "ROW-1"],
                    "meta": {
                        "chartId": chart.id,
                        "width": 12,
                        "height": 70,
                        "sliceName": chart.slice_name,
                    },
                },
            }
        )
        db.session.add(dashboard)
        db.session.commit()
    ids = dict(
        database_id=database.id, dataset_id=dataset.id, chart_id=chart.id, dashboard_id=dashboard.id
    )
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
sql = "SELECT mktsegment, count(*) AS customer_count FROM lakehouse.bronze.customer GROUP BY mktsegment ORDER BY customer_count DESC"
r = s.post(
    base + "/api/v1/sqllab/execute/",
    json=dict(
        database_id=ids["database_id"],
        schema="bronze",
        sql=sql,
        runAsync=False,
        json=True,
        queryLimit=100,
    ),
)
r.raise_for_status()
result = r.json()
if result.get("status") != "success":
    raise RuntimeError(str(result))
print(
    "LAB_RESULT "
    + json.dumps(
        dict(
            ids=ids,
            sql=sql,
            status=result["status"],
            data=result.get("data"),
            columns=result.get("columns"),
        )
    )
)
r = s.get(base + f"/api/v1/chart/{ids['chart_id']}")
r.raise_for_status()
print("CHART_STATUS", r.status_code)
r = s.get(base + "/superset/dashboard/lakehouse-q3/")
print("DASHBOARD_HTTP", r.status_code)

metric = dict(
    expressionType="SQL", sqlExpression="SUM(revenue)", label="Revenue", optionName="metric_revenue"
)
payload = dict(
    datasource=dict(id=ids["dataset_id"], type="table"),
    queries=[dict(columns=["orderkey"], metrics=[metric], orderby=[[metric, False]], row_limit=10)],
    result_format="json",
    result_type="full",
)
r = s.post(base + "/api/v1/chart/data", json=payload)
r.raise_for_status()
result = r.json()
assert len(result["result"][0]["data"]) == 10, result
print("CHART_DATA " + json.dumps(result["result"][0]["data"]))
