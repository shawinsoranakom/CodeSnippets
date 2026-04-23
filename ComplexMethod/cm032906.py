def get_metadata_filter_expression(metadata_filtering_conditions: dict) -> str:
    """
    Convert metadata filtering conditions to MySQL JSON path expression.

    Args:
        metadata_filtering_conditions: dict with 'conditions' and 'logical_operator' keys

    Returns:
        MySQL JSON path expression string
    """
    if not metadata_filtering_conditions:
        return ""

    conditions = metadata_filtering_conditions.get("conditions", [])
    logical_operator = metadata_filtering_conditions.get("logical_operator", "and").upper()

    if not conditions:
        return ""

    if logical_operator not in ["AND", "OR"]:
        raise ValueError(f"Unsupported logical operator: {logical_operator}. Only 'and' and 'or' are supported.")

    metadata_filters = []
    for condition in conditions:
        name = condition.get("name")
        comparison_operator = condition.get("comparison_operator")
        value = condition.get("value")

        if not all([name, comparison_operator]):
            continue

        expr = f"JSON_EXTRACT(metadata, '$.{name}')"
        value_str = get_value_str(value)

        # Convert comparison operator to MySQL JSON path syntax
        if comparison_operator == "is":
            # JSON_EXTRACT(metadata, '$.field_name') = 'value'
            metadata_filters.append(f"{expr} = {value_str}")
        elif comparison_operator == "is not":
            metadata_filters.append(f"{expr} != {value_str}")
        elif comparison_operator == "contains":
            metadata_filters.append(f"JSON_CONTAINS({expr}, {value_str})")
        elif comparison_operator == "not contains":
            metadata_filters.append(f"NOT JSON_CONTAINS({expr}, {value_str})")
        elif comparison_operator == "start with":
            metadata_filters.append(f"{expr} LIKE CONCAT({value_str}, '%')")
        elif comparison_operator == "end with":
            metadata_filters.append(f"{expr} LIKE CONCAT('%', {value_str})")
        elif comparison_operator == "empty":
            metadata_filters.append(f"({expr} IS NULL OR {expr} = '' OR {expr} = '[]' OR {expr} = '{{}}')")
        elif comparison_operator == "not empty":
            metadata_filters.append(f"({expr} IS NOT NULL AND {expr} != '' AND {expr} != '[]' AND {expr} != '{{}}')")
        # Number operators
        elif comparison_operator == "=":
            metadata_filters.append(f"CAST({expr} AS DECIMAL(20,10)) = {value_str}")
        elif comparison_operator == "≠":
            metadata_filters.append(f"CAST({expr} AS DECIMAL(20,10)) != {value_str}")
        elif comparison_operator == ">":
            metadata_filters.append(f"CAST({expr} AS DECIMAL(20,10)) > {value_str}")
        elif comparison_operator == "<":
            metadata_filters.append(f"CAST({expr} AS DECIMAL(20,10)) < {value_str}")
        elif comparison_operator == "≥":
            metadata_filters.append(f"CAST({expr} AS DECIMAL(20,10)) >= {value_str}")
        elif comparison_operator == "≤":
            metadata_filters.append(f"CAST({expr} AS DECIMAL(20,10)) <= {value_str}")
        # Time operators
        elif comparison_operator == "before":
            metadata_filters.append(f"CAST({expr} AS DATETIME) < {value_str}")
        elif comparison_operator == "after":
            metadata_filters.append(f"CAST({expr} AS DATETIME) > {value_str}")
        else:
            logger.warning(f"Unsupported comparison operator: {comparison_operator}")
            continue

    if not metadata_filters:
        return ""

    return f"({f' {logical_operator} '.join(metadata_filters)})"