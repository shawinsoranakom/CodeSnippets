async def test_brightness_mode(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the LaMetric brightness mode controls."""
    state = hass.states.get("select.frenck_s_lametric_brightness_mode")
    assert state
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME) == "Frenck's LaMetric Brightness mode"
    )
    assert state.attributes.get(ATTR_OPTIONS) == ["auto", "manual"]
    assert state.state == BrightnessMode.AUTO

    entry = entity_registry.async_get(state.entity_id)
    assert entry
    assert entry.device_id
    assert entry.entity_category is EntityCategory.CONFIG
    assert entry.unique_id == "SA110405124500W00BS9-brightness_mode"

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
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.frenck_s_lametric_brightness_mode",
            ATTR_OPTION: "manual",
        },
        blocking=True,
    )

    assert len(mock_lametric.display.mock_calls) == 1
    mock_lametric.display.assert_called_once_with(brightness_mode=BrightnessMode.MANUAL)