async def test_rokutv_sensors(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    mock_roku: MagicMock,
) -> None:
    """Test the Roku TV sensors."""
    state = hass.states.get("sensor.58_onn_roku_tv_active_app")
    entry = entity_registry.async_get("sensor.58_onn_roku_tv_active_app")
    assert entry
    assert state
    assert entry.unique_id == "YN00H5555555_active_app"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert state.state == "Antenna TV"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == '58" Onn Roku TV Active app'
    assert ATTR_DEVICE_CLASS not in state.attributes

    state = hass.states.get("sensor.58_onn_roku_tv_active_app_id")
    entry = entity_registry.async_get("sensor.58_onn_roku_tv_active_app_id")
    assert entry
    assert state
    assert entry.unique_id == "YN00H5555555_active_app_id"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert state.state == "tvinput.dtv"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == '58" Onn Roku TV Active app ID'
    assert ATTR_DEVICE_CLASS not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, "YN00H5555555")}
    assert device_entry.connections == {
        (dr.CONNECTION_NETWORK_MAC, "d8:13:99:f8:b0:c6"),
        (dr.CONNECTION_NETWORK_MAC, "d4:3a:2e:07:fd:cb"),
    }
    assert device_entry.manufacturer == "Onn"
    assert device_entry.model == "100005844"
    assert device_entry.name == '58" Onn Roku TV'
    assert device_entry.entry_type is None
    assert device_entry.sw_version == "9.2.0"
    assert device_entry.hw_version == "7820X"
    assert (
        device_entry.area_id == area_registry.async_get_area_by_name("Living room").id
    )