async def test_bluetooth(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the LaMetric Bluetooth control."""
    state = hass.states.get("switch.frenck_s_lametric_bluetooth")
    assert state
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Frenck's LaMetric Bluetooth"
    assert state.state == STATE_OFF

    entry = entity_registry.async_get(state.entity_id)
    assert entry
    assert entry.device_id
    assert entry.entity_category is EntityCategory.CONFIG
    assert entry.unique_id == "SA110405124500W00BS9-bluetooth"

    device = device_registry.async_get(entry.device_id)
    assert device
    assert device.configuration_url == "https://127.0.0.1/"
    assert device.connections == {
        (dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff"),
        (dr.CONNECTION_BLUETOOTH, "aa:bb:cc:dd:ee:ee"),
    }
    assert device.entry_type is None
    assert device.hw_version is None
    assert device.identifiers == {(DOMAIN, "SA110405124500W00BS9")}
    assert device.manufacturer == "LaMetric Inc."
    assert device.name == "Frenck's LaMetric"
    assert device.serial_number == "SA110405124500W00BS9"
    assert device.sw_version == "2.2.2"

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "switch.frenck_s_lametric_bluetooth",
        },
        blocking=True,
    )

    assert len(mock_lametric.bluetooth.mock_calls) == 1
    mock_lametric.bluetooth.assert_called_once_with(active=True)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "switch.frenck_s_lametric_bluetooth",
        },
        blocking=True,
    )

    assert len(mock_lametric.bluetooth.mock_calls) == 2
    mock_lametric.bluetooth.assert_called_with(active=False)

    mock_lametric.device.return_value.bluetooth.available = False
    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    state = hass.states.get("switch.frenck_s_lametric_bluetooth")
    assert state
    assert state.state == STATE_UNAVAILABLE