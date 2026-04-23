async def test_primary_config_entry(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the primary integration field."""
    mock_config_entry_1 = MockConfigEntry(domain="mqtt", title=None)
    mock_config_entry_1.add_to_hass(hass)
    mock_config_entry_2 = MockConfigEntry(title=None)
    mock_config_entry_2.add_to_hass(hass)
    mock_config_entry_3 = MockConfigEntry(title=None)
    mock_config_entry_3.add_to_hass(hass)
    mock_config_entry_4 = MockConfigEntry(domain="matter", title=None)
    mock_config_entry_4.add_to_hass(hass)

    # Create device without model name etc, config entry will not be marked primary
    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers=set(),
    )
    assert device.primary_config_entry is None

    # Set model, mqtt config entry will be promoted to primary
    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        model="model",
    )
    assert device.primary_config_entry == mock_config_entry_1.entry_id

    # New config entry with model will be promoted to primary
    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_2.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        model="model 2",
    )
    assert device.primary_config_entry == mock_config_entry_2.entry_id

    # New config entry with model will not be promoted to primary
    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_3.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        model="model 3",
    )
    assert device.primary_config_entry == mock_config_entry_2.entry_id

    # New matter config entry with model will not be promoted to primary
    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_4.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        model="model 3",
    )
    assert device.primary_config_entry == mock_config_entry_2.entry_id

    # Remove the primary config entry
    device = device_registry.async_update_device(
        device.id,
        remove_config_entry_id=mock_config_entry_2.entry_id,
    )
    assert device.primary_config_entry is None

    # Create new
    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers=set(),
        manufacturer="manufacturer",
        model="model",
    )
    assert device.primary_config_entry == mock_config_entry_1.entry_id