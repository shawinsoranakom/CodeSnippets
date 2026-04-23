def resolve_slot_data(key: str, request: dict[str, Any]) -> dict[str, str]:
    """Check slot request for synonym resolutions."""
    # Default to the spoken slot value if more than one or none are found. Always
    # passes the id and name of the nearest possible slot resolution. For
    # reference to the request object structure, see the Alexa docs:
    # https://tinyurl.com/ybvm7jhs
    resolved_data: dict[str, Any] = {}
    resolved_data["value"] = request["value"]
    resolved_data["id"] = ""

    if (
        "resolutions" in request
        and "resolutionsPerAuthority" in request["resolutions"]
        and len(request["resolutions"]["resolutionsPerAuthority"]) >= 1
    ):
        # Extract all of the possible values from each authority with a
        # successful match
        possible_values = []

        for entry in request["resolutions"]["resolutionsPerAuthority"]:
            if entry["status"]["code"] != SYN_RESOLUTION_MATCH:
                continue

            possible_values.extend([item["value"] for item in entry["values"]])

        # Always set id if available, otherwise an empty string is used as id
        if len(possible_values) >= 1:
            # Set ID if available
            if "id" in possible_values[0]:
                resolved_data["id"] = possible_values[0]["id"]

        # If there is only one match use the resolved value, otherwise the
        # resolution cannot be determined, so use the spoken slot value and empty string as id
        if len(possible_values) == 1:
            resolved_data["value"] = possible_values[0]["name"]
        else:
            _LOGGER.debug(
                "Found multiple synonym resolutions for slot value: {%s: %s}",
                key,
                resolved_data["value"],
            )

    return resolved_data