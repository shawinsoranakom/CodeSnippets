def validate_event_data(obj: dict) -> dict:
    """Validate that a trigger has a valid event data."""
    # Return if there's no event data to validate
    if ATTR_EVENT_DATA not in obj:
        return obj

    event_source: str = obj[ATTR_EVENT_SOURCE]
    event_name: str = obj[ATTR_EVENT]
    event_data: dict = obj[ATTR_EVENT_DATA]
    try:
        if event_source == "controller":
            CONTROLLER_EVENT_MODEL_MAP[event_name](**event_data)
        elif event_source == "driver":
            DRIVER_EVENT_MODEL_MAP[event_name](**event_data)
        else:
            NODE_EVENT_MODEL_MAP[event_name](**event_data)
    except ValidationError as exc:
        # Filter out required field errors if keys can be missing, and if there are
        # still errors, raise an exception
        if [error for error in exc.errors() if error["type"] != "missing"]:
            raise vol.MultipleInvalid from exc
    return obj