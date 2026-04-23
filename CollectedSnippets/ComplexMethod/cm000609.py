def _apply_filter(
    cell_value: str,
    filter_value: str,
    operator: FilterOperator,
    match_case: bool,
) -> bool:
    """Apply a filter condition to a cell value."""
    if operator == FilterOperator.IS_EMPTY:
        return cell_value.strip() == ""
    if operator == FilterOperator.IS_NOT_EMPTY:
        return cell_value.strip() != ""

    # For comparison operators, apply case sensitivity
    compare_cell = cell_value if match_case else cell_value.lower()
    compare_filter = filter_value if match_case else filter_value.lower()

    if operator == FilterOperator.EQUALS:
        return compare_cell == compare_filter
    elif operator == FilterOperator.NOT_EQUALS:
        return compare_cell != compare_filter
    elif operator == FilterOperator.CONTAINS:
        return compare_filter in compare_cell
    elif operator == FilterOperator.NOT_CONTAINS:
        return compare_filter not in compare_cell
    elif operator in (
        FilterOperator.GREATER_THAN,
        FilterOperator.LESS_THAN,
        FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN_OR_EQUAL,
    ):
        # Try numeric comparison first
        try:
            num_cell = float(cell_value)
            num_filter = float(filter_value)
            if operator == FilterOperator.GREATER_THAN:
                return num_cell > num_filter
            elif operator == FilterOperator.LESS_THAN:
                return num_cell < num_filter
            elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                return num_cell >= num_filter
            elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
                return num_cell <= num_filter
        except ValueError:
            # Fall back to string comparison
            if operator == FilterOperator.GREATER_THAN:
                return compare_cell > compare_filter
            elif operator == FilterOperator.LESS_THAN:
                return compare_cell < compare_filter
            elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                return compare_cell >= compare_filter
            elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
                return compare_cell <= compare_filter

    return False