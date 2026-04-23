async def async_manipulate_test_data(
    hass: HomeAssistant,
    hmip_device: HomeMaticIPObject,
    attribute: str,
    new_value: Any,
    channel: int = 1,
    fire_device: HomeMaticIPObject | None = None,
    channel_real_index: int | None = None,
):
    """Set new value on hmip device."""
    if channel == 1:
        setattr(hmip_device, attribute, new_value)

    channels = getattr(hmip_device, "functionalChannels", None)
    if channels:
        if channel_real_index is not None:
            functional_channel = next(
                (ch for ch in channels if ch.index == channel_real_index),
                None,
            )
            assert functional_channel is not None, (
                f"No functional channel with index {channel_real_index} found in hmip_device.functionalChannels"
            )
        else:
            functional_channel = channels[channel]

        setattr(functional_channel, attribute, new_value)

    fire_target = hmip_device if fire_device is None else fire_device

    if isinstance(fire_target, AsyncHome):
        fire_target.fire_update_event(fire_target._rawJSONData)
    else:
        fire_target.fire_update_event()

    await hass.async_block_till_done()