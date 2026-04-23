def convert_condition(time: str, weather: tuple[tuple[str, int | None], ...]) -> str:
    """Convert NWS codes to HA condition.

    Choose first condition in CONDITION_CLASSES that exists in weather code.
    If no match is found, return first condition from NWS
    """
    conditions: list[str] = [w[0] for w in weather]

    # Choose condition with highest priority.
    cond = next(
        (
            key
            for key, value in CONDITION_CLASSES.items()
            if any(condition in value for condition in conditions)
        ),
        conditions[0],
    )

    if cond == "clear":
        if time == "day":
            return ATTR_CONDITION_SUNNY
        if time == "night":
            return ATTR_CONDITION_CLEAR_NIGHT
    return cond