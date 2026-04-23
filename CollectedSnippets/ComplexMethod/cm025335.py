def is_block_momentary_input(
    settings: dict[str, Any], block: Block, include_detached: bool = False
) -> bool:
    """Return true if block input button settings is set to a momentary type."""
    momentary_types = ["momentary", "momentary_on_release"]

    if include_detached:
        momentary_types.append("detached")

    # Shelly Button type is fixed to momentary and no btn_type
    if settings["device"]["type"] in SHBTN_MODELS:
        return True

    if settings.get("mode") == "roller":
        button_type = settings["rollers"][0]["button_type"]
        return button_type in momentary_types

    button = settings.get("relays") or settings.get("lights") or settings.get("inputs")
    if button is None:
        return False

    # Shelly 1L has two button settings in the first channel
    if settings["device"]["type"] == MODEL_1L:
        channel = int(block.channel or 0) + 1
        button_type = button[0].get("btn" + str(channel) + "_type")
    else:
        # Some devices has only one channel in settings
        channel = min(int(block.channel or 0), len(button) - 1)
        button_type = button[channel].get("btn_type")

    return button_type in momentary_types