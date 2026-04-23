async def test_roku_binary_sensors(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the Roku binary sensors."""
    state = hass.states.get("binary_sensor.my_roku_3_headphones_connected")
    entry = entity_registry.async_get("binary_sensor.my_roku_3_headphones_connected")
    assert entry
    assert state
    assert entry.unique_id == f"{UPNP_SERIAL}_headphones_connected"
    assert entry.entity_category is None
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Roku 3 Headphones connected"
    assert ATTR_DEVICE_CLASS not in state.attributes

    state = hass.states.get("binary_sensor.my_roku_3_supports_airplay")
    entry = entity_registry.async_get("binary_sensor.my_roku_3_supports_airplay")
    assert entry
    assert state
    assert entry.unique_id == f"{UPNP_SERIAL}_supports_airplay"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Roku 3 Supports AirPlay"
    assert ATTR_DEVICE_CLASS not in state.attributes

    state = hass.states.get("binary_sensor.my_roku_3_supports_ethernet")
    entry = entity_registry.async_get("binary_sensor.my_roku_3_supports_ethernet")
    assert entry
    assert state
    assert entry.unique_id == f"{UPNP_SERIAL}_supports_ethernet"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Roku 3 Supports Ethernet"
    assert ATTR_DEVICE_CLASS not in state.attributes

    state = hass.states.get("binary_sensor.my_roku_3_supports_find_remote")
    entry = entity_registry.async_get("binary_sensor.my_roku_3_supports_find_remote")
    assert entry
    assert state
    assert entry.unique_id == f"{UPNP_SERIAL}_supports_find_remote"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Roku 3 Supports find remote"
    assert ATTR_DEVICE_CLASS not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, UPNP_SERIAL)}
    assert device_entry.connections == {
        (dr.CONNECTION_NETWORK_MAC, "b0:a7:37:96:4d:fb"),
        (dr.CONNECTION_NETWORK_MAC, "b0:a7:37:96:4d:fa"),
    }
    assert device_entry.manufacturer == "Roku"
    assert device_entry.model == "Roku 3"
    assert device_entry.name == "My Roku 3"
    assert device_entry.entry_type is None
    assert device_entry.sw_version == "7.5.0"
    assert device_entry.hw_version == "4200X"
    assert device_entry.area_id is None