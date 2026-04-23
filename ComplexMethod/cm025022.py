async def test_get_or_create_empty_then_update(
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test creating an entry, then setting name, model, manufacturer."""
    entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    assert entry.name is None
    assert entry.model is None
    assert entry.manufacturer is None

    entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        name="name 1",
        model="model 1",
        manufacturer="manufacturer 1",
    )
    assert entry.name == "name 1"
    assert entry.model == "model 1"
    assert entry.manufacturer == "manufacturer 1"

    entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        default_name="default name 1",
        default_model="default model 1",
        default_manufacturer="default manufacturer 1",
    )
    assert entry.name == "name 1"
    assert entry.model == "model 1"
    assert entry.manufacturer == "manufacturer 1"