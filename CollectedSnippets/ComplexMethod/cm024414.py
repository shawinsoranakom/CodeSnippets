async def test_options_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # test save invalid uuid
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "new_uuid": "invalid",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {"new_uuid": "invalid_uuid_format"}

    # test save new uuid
    uuid = "daa4b6bb-b77a-4662-aeb8-b3ed56454091"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "new_uuid": uuid,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ALLOW_NAMELESS_UUIDS: [uuid]}

    # test save duplicate uuid
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ALLOW_NAMELESS_UUIDS: [uuid],
            "new_uuid": uuid,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ALLOW_NAMELESS_UUIDS: [uuid]}

    # delete
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ALLOW_NAMELESS_UUIDS: [],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ALLOW_NAMELESS_UUIDS: []}