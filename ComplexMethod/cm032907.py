def get_filters(condition: dict) -> list[str]:
    filters: list[str] = []
    for k, v in condition.items():
        if not v:
            continue

        if k == "exists":
            filters.append(f"{v} IS NOT NULL")
        elif k == "must_not" and isinstance(v, dict) and "exists" in v:
            filters.append(f"{v.get('exists')} IS NULL")
        elif k == "metadata_filtering_conditions":
            # Handle metadata filtering conditions
            metadata_filter = get_metadata_filter_expression(v)
            if metadata_filter:
                filters.append(metadata_filter)
        elif k in array_columns:
            if isinstance(v, list):
                array_filters = []
                for vv in v:
                    array_filters.append(f"array_contains({k}, {get_value_str(vv)})")
                array_filter = " OR ".join(array_filters)
                filters.append(f"({array_filter})")
            else:
                filters.append(f"array_contains({k}, {get_value_str(v)})")
        elif isinstance(v, list):
            values: list[str] = []
            for item in v:
                values.append(get_value_str(item))
            value = ", ".join(values)
            filters.append(f"{k} IN ({value})")
        else:
            filters.append(f"{k} = {get_value_str(v)}")
    return filters