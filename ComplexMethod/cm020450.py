async def test_async_step_reconfigure_options(hass: HomeAssistant) -> None:
    """Test reconfig options: change MediumType from air to fresh water."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        title="TD40/TD200 7510",
        data={CONF_MEDIUM_TYPE: MediumType.AIR.value},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.data[CONF_MEDIUM_TYPE] == MediumType.AIR.value

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema: vol.Schema = result["data_schema"]
    medium_type_key = next(
        iter(key for key in schema.schema if key == CONF_MEDIUM_TYPE)
    )
    assert medium_type_key.default() == MediumType.AIR.value

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY

    # Verify the new configuration
    assert entry.data[CONF_MEDIUM_TYPE] == MediumType.FRESH_WATER.value