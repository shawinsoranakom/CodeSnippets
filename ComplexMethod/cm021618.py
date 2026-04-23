async def test_volume(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the LaMetric volume controls."""
    state = hass.states.get("number.frenck_s_lametric_volume")
    assert state
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Frenck's LaMetric Volume"
    assert state.attributes.get(ATTR_MAX) == 100
    assert state.attributes.get(ATTR_MIN) == 0
    assert state.attributes.get(ATTR_STEP) == 1
    assert state.state == "100"

    entry = entity_registry.async_get(state.entity_id)
    assert entry
    assert entry.device_id
    assert entry.entity_category is EntityCategory.CONFIG
    assert entry.unique_id == "SA110405124500W00BS9-volume"

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
    assert device.sw_version == "2.2.2"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: "number.frenck_s_lametric_volume",
            ATTR_VALUE: 42,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(mock_lametric.audio.mock_calls) == 1
    mock_lametric.audio.assert_called_once_with(volume=42)