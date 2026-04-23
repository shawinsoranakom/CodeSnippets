def filter_fields(data):
    """return all field names used in global filter definitions"""
    fields_by_model = defaultdict(set)
    charts = odoo_charts(data)
    if "odooVersion" in data and data["odooVersion"] < 5:
        for filter_definition in data.get("globalFilters", []):
            for pivot_id, matching in filter_definition.get("pivotFields", dict()).items():
                model = data["pivots"][pivot_id]["model"]
                fields_by_model[model].add(matching["field"])
            for list_id, matching in filter_definition.get("listFields", dict()).items():
                model = data["lists"][list_id]["model"]
                fields_by_model[model].add(matching["field"])
            for chart_id, matching in filter_definition.get("graphFields", dict()).items():
                chart = next((chart for chart in charts if chart["id"] == chart_id), None)
                model = chart["metaData"]["resModel"]
                fields_by_model[model].add(matching["field"])
    else:
        for pivot in data.get("pivots", {}).values():
            if pivot.get("type", "ODOO") == "ODOO":
                model = pivot["model"]
                field = pivot.get("fieldMatching", {}).get("chain")
                if field:
                    fields_by_model[model].add(field)
        for _list in data.get("lists", {}).values():
            model = _list["model"]
            field = _list.get("fieldMatching", {}).get("chain")
            if field:
                fields_by_model[model].add(field)
        for chart in charts:
            model = chart["metaData"]["resModel"]
            field = chart.get("fieldMatching", {}).get("chain")
            if field:
                fields_by_model[model].add(field)

    return dict(fields_by_model)