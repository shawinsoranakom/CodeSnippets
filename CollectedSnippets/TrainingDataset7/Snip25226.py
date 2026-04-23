def inspectdb_views_only(table_name):
    return table_name.startswith("inspectdb_") and table_name.endswith(
        ("_materialized", "_view")
    )