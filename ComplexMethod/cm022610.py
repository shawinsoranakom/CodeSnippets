async def test_options_flow(
    hass: HomeAssistant,
    mock_is_allowed_path: bool,
    platform: str,
    data: dict[str, Any],
    options: dict[str, Any],
    new_options: dict[str, Any],
) -> None:
    """Test options config flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=data, options=options, version=2)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=new_options,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == new_options

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert entry.options == new_options