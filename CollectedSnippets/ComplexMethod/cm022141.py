async def test_options_flow(hass: HomeAssistant, loaded_entry: MockConfigEntry) -> None:
    """Test options flow."""

    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_BROADCAST_ADDRESS: "192.168.255.255",
            CONF_BROADCAST_PORT: 10,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_MAC: DEFAULT_MAC,
        CONF_BROADCAST_ADDRESS: "192.168.255.255",
        CONF_BROADCAST_PORT: 10,
    }

    await hass.async_block_till_done()

    assert loaded_entry.options == {
        CONF_MAC: DEFAULT_MAC,
        CONF_BROADCAST_ADDRESS: "192.168.255.255",
        CONF_BROADCAST_PORT: 10,
    }

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 1

    state = hass.states.get("button.wake_on_lan_00_01_02_03_04_05")
    assert state is not None