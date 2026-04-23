async def setup_config_entry(
    hass: HomeAssistant,
    data: dict[str, Any],
    unique_id: str = "any",
    device: Mock | None = None,
    fritz: Mock | None = None,
    template: Mock | None = None,
    trigger: Mock | None = None,
) -> MockConfigEntry:
    """Do setup of a MockConfigEntry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        unique_id=unique_id,
    )
    entry.add_to_hass(hass)
    if device is not None and fritz is not None:
        fritz().get_devices.return_value = [device]

    if template is not None and fritz is not None:
        fritz().get_templates.return_value = [template]

    if trigger is not None and fritz is not None:
        fritz().get_triggers.return_value = [trigger]

    await hass.config_entries.async_setup(entry.entry_id)
    if device is not None:
        await hass.async_block_till_done()
    return entry