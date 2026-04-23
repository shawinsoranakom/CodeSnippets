async def test_setting_change(
    hass: HomeAssistant, config_entry: MockConfigEntry, entity_registry: EntityRegistry
) -> None:
    """Test if the state of the switches are updated when an update message from the websocket comes in."""
    integration = await init_integration(hass, config_entry, Platform.SWITCH)
    client_mock = integration[0]

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    for switch in entity_entries:
        state = hass.states.get(switch.entity_id)
        assert state.state == STATE_OFF

    await client_mock.update_charge_point(
        "101",
        CHARGEPOINT_SETTINGS,
        {
            PLUG_AND_CHARGE: True,
            PUBLIC_CHARGING: {"value": False, "permission": "write"},
        },
    )

    charge_cards_only_switch = hass.states.get("switch.101_linked_charging_cards_only")
    assert charge_cards_only_switch.state == STATE_ON

    plug_and_charge_switch = hass.states.get("switch.101_plug_charge")
    assert plug_and_charge_switch.state == STATE_ON

    plug_and_charge_switch = hass.states.get("switch.101_block_charge_point")
    assert plug_and_charge_switch.state == STATE_OFF

    await client_mock.update_charge_point(
        "101", CHARGEPOINT_STATUS, {ACTIVITY: UNAVAILABLE}
    )

    charge_cards_only_switch = hass.states.get("switch.101_linked_charging_cards_only")
    assert charge_cards_only_switch.state == STATE_UNAVAILABLE

    plug_and_charge_switch = hass.states.get("switch.101_plug_charge")
    assert plug_and_charge_switch.state == STATE_UNAVAILABLE

    switch = hass.states.get("switch.101_block_charge_point")
    assert switch.state == STATE_ON