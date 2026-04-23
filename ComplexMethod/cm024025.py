async def test_options_flow_linux(hass: HomeAssistant) -> None:
    """Test options on Linux."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={},
        unique_id="00:00:00:00:00:01",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] is None

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSIVE: True,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_PASSIVE] is True

    # Verify we can change it to False

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] is None

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSIVE: False,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_PASSIVE] is False
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()