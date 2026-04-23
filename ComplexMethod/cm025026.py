async def test_device_registry_connections_collision(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test connection collisions in the device registry."""
    config_entry = MockConfigEntry()
    config_entry.add_to_hass(hass)

    device1 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "none")},
        manufacturer="manufacturer",
        model="model",
    )
    device2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "none")},
        manufacturer="manufacturer",
        model="model",
    )

    assert device1.id == device2.id

    device3 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )

    # Attempt to merge connection for device3 with the same
    # connection that already exists in device1
    with pytest.raises(
        HomeAssistantError, match=f"Connections.*already registered.*{device1.id}"
    ):
        device_registry.async_update_device(
            device3.id,
            merge_connections={
                (dr.CONNECTION_NETWORK_MAC, "EE:EE:EE:EE:EE:EE"),
                (dr.CONNECTION_NETWORK_MAC, "none"),
            },
        )

    # Attempt to add new connections for device3 with the same
    # connection that already exists in device1
    with pytest.raises(
        HomeAssistantError, match=f"Connections.*already registered.*{device1.id}"
    ):
        device_registry.async_update_device(
            device3.id,
            new_connections={
                (dr.CONNECTION_NETWORK_MAC, "EE:EE:EE:EE:EE:EE"),
                (dr.CONNECTION_NETWORK_MAC, "none"),
            },
        )

    device3_refetched = device_registry.async_get(device3.id)
    assert device3_refetched.connections == set()
    assert device3_refetched.identifiers == {("bridgeid", "0123")}

    device1_refetched = device_registry.async_get(device1.id)
    assert device1_refetched.connections == {(dr.CONNECTION_NETWORK_MAC, "none")}
    assert device1_refetched.identifiers == set()

    device2_refetched = device_registry.async_get(device2.id)
    assert device2_refetched.connections == {(dr.CONNECTION_NETWORK_MAC, "none")}
    assert device2_refetched.identifiers == set()

    assert device2_refetched.id == device1_refetched.id
    assert len(device_registry.devices) == 2

    # Attempt to implicitly merge connection for device3 with the same
    # connection that already exists in device1
    device4 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("bridgeid", "0123")},
        connections={
            (dr.CONNECTION_NETWORK_MAC, "EE:EE:EE:EE:EE:EE"),
            (dr.CONNECTION_NETWORK_MAC, "none"),
        },
    )
    assert len(device_registry.devices) == 2
    assert device4.id in (device1.id, device3.id)

    device3_refetched = device_registry.async_get(device3.id)
    device1_refetched = device_registry.async_get(device1.id)
    assert not device1_refetched.connections.isdisjoint(device3_refetched.connections)