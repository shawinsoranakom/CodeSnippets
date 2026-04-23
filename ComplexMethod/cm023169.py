async def test_opening_state_disables_legacy_window_door_notification_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    hoppe_ehandle_connectsense_state,
) -> None:
    """Test Opening state disables legacy Access Control window/door sensors."""
    node = Node(
        client,
        _add_door_tilt_state_value(hoppe_ehandle_connectsense_state),
    )
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    legacy_entries = [
        entry
        for entry in entity_registry.entities.values()
        if entry.domain == "binary_sensor"
        and entry.platform == "zwave_js"
        and (
            entry.original_name
            in {
                "Window/door is open",
                "Window/door is closed",
                "Window/door is open in regular position",
                "Window/door is open in tilt position",
            }
            or (
                entry.original_name == "Window/door is tilted"
                and entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
            )
        )
    ]

    assert len(legacy_entries) == 7
    assert all(
        entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        for entry in legacy_entries
    )
    assert all(hass.states.get(entry.entity_id) is None for entry in legacy_entries)

    open_state = hass.states.get("binary_sensor.ehandle_connectsense")
    assert open_state is not None
    assert open_state.state == STATE_OFF
    assert open_state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.DOOR