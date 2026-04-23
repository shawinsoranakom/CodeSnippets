async def test_roku_sensors(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the Roku sensors."""
    state = hass.states.get("sensor.my_roku_3_active_app")
    entry = entity_registry.async_get("sensor.my_roku_3_active_app")
    assert entry
    assert state
    assert entry.unique_id == f"{UPNP_SERIAL}_active_app"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert state.state == "Roku"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Roku 3 Active app"
    assert ATTR_DEVICE_CLASS not in state.attributes

    state = hass.states.get("sensor.my_roku_3_active_app_id")
    entry = entity_registry.async_get("sensor.my_roku_3_active_app_id")
    assert entry
    assert state
    assert entry.unique_id == f"{UPNP_SERIAL}_active_app_id"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Roku 3 Active app ID"
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