def get_block_input_triggers(
    device: BlockDevice, block: Block
) -> list[tuple[str, str]]:
    """Return list of input triggers for block."""
    if "inputEvent" not in block.sensor_ids or "inputEventCnt" not in block.sensor_ids:
        return []

    if not is_block_momentary_input(device.settings, block, True):
        return []

    if block.type == "device" or get_block_number_of_channels(device, block) == 1:
        subtype = "button"
    else:
        assert block.channel
        subtype = f"button{int(block.channel) + 1}"

    if device.settings["device"]["type"] in SHBTN_MODELS:
        trigger_types = SHBTN_INPUTS_EVENTS_TYPES
    elif device.settings["device"]["type"] == MODEL_I3:
        trigger_types = SHIX3_1_INPUTS_EVENTS_TYPES
    else:
        trigger_types = BASIC_INPUTS_EVENTS_TYPES

    return [(trigger_type, subtype) for trigger_type in trigger_types]