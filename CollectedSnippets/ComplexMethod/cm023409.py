async def test_setup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test setup with basic config."""
    state = hass.states.get(MAIN_ENTITY_ID)
    entry = entity_registry.async_get(MAIN_ENTITY_ID)

    assert state
    assert entry
    assert entry.original_device_class is MediaPlayerDeviceClass.RECEIVER
    assert entry.unique_id == "1GU48T017973"

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, "1GU48T017973")}
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