def build_time_period_params(
    constraints_response: dict | None,
) -> tuple[list[dict], str | None]:
    """
    Build time period parameters from a constraints API response.

    Extracts start date, end date, and series count from annotations.

    Parameters
    ----------
    constraints_response : dict | None
        The response from get_available_constraints

    Returns
    -------
    tuple[list[dict], str | None]
        A tuple of (options list, series_count) where options contains
        start/end date dicts with 'label' and 'value' keys.
    """
    if not constraints_response:
        return [], None

    full_response = constraints_response.get("full_response", {})
    content_constraints = full_response.get("data", {}).get("contentConstraints", [])
    annotations = (
        content_constraints[0].get("annotations", []) if content_constraints else []
    )

    start = end = series_count = None
    for annotation in annotations:
        ann_id = annotation.get("id")
        if ann_id == "time_period_start":
            start = annotation.get("title")
        elif ann_id == "time_period_end":
            end = annotation.get("title")
        elif ann_id == "series_count":
            series_count = annotation.get("title")

    options: list[dict] = []
    if start:
        options.append({"label": f"Start Date: {start}", "value": start})
    if end:
        options.append({"label": f"End Date: {end}", "value": end})

    return options, series_count