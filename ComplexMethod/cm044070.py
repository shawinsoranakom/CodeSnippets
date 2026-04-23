def set_parameter_type(p: dict, p_schema: dict):
    """
    Determine and set the type for the parameter.

    Parameters
    ----------
    p : Dict
        Processed parameter dictionary.
    p_schema : Dict
        Schema dictionary for the parameter.
    """
    p_type = p_schema.get("type") if not p.get("type") else p.get("type")

    if p_type == "string":
        p["type"] = "text"

    if p_type in ("float", "integer") or (
        not isinstance(p["value"], bool) and isinstance(p["value"], (int, float))
    ):
        p["type"] = "number"

    if (
        p_type == "boolean"
        or p_schema.get("type") == "boolean"
        or ("anyOf" in p_schema and p_schema["anyOf"][0].get("type") == "boolean")
    ):
        p["type"] = "boolean"

    if p["parameter_name"] == "date" or "_date" in p["parameter_name"]:
        p["type"] = "date"

    if "timeframe" in p["parameter_name"]:
        p["type"] = "text"

    if p["parameter_name"] == "limit":
        p["type"] = "number"

    if p.get("type") in ("array", "list") or isinstance(p.get("type"), (list, dict)):
        p["type"] = "text"

    return p