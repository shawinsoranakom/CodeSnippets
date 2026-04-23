async def test_infrared_fan_subentry_flow(hass: HomeAssistant) -> None:
    """Test infrared fan subentry flow creates an entry."""
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "infrared_fan"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": "Living Room Fan",
            "infrared_entity_id": ENTITY_IR_TRANSMITTER,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    subentry_id = [
        sid
        for sid, s in config_entry.subentries.items()
        if s.subentry_type == "infrared_fan"
    ][0]
    assert config_entry.subentries[subentry_id] == config_entries.ConfigSubentry(
        data={"infrared_entity_id": ENTITY_IR_TRANSMITTER},
        subentry_id=subentry_id,
        subentry_type="infrared_fan",
        title="Living Room Fan",
        unique_id=None,
    )