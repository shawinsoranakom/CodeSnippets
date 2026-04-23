async def test_container_stack_device_links(
    hass: HomeAssistant,
    mock_portainer_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test that stack-linked containers are nested under the correct stack device."""
    await setup_integration(hass, mock_config_entry)

    endpoint_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{mock_config_entry.entry_id}_1")}
    )
    assert endpoint_device is not None

    dashy_stack_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{mock_config_entry.entry_id}_1_stack_2")}
    )
    assert dashy_stack_device is not None
    assert dashy_stack_device.via_device_id == endpoint_device.id

    webstack_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{mock_config_entry.entry_id}_1_stack_1")}
    )
    assert webstack_device is not None
    assert webstack_device.via_device_id == endpoint_device.id

    swarm_container_device = device_registry.async_get_device(
        identifiers={
            (
                DOMAIN,
                f"{mock_config_entry.entry_id}_1_dashy_dashy.1.qgza68hnz4n1qvyz3iohynx05",
            )
        }
    )
    assert swarm_container_device is not None
    assert swarm_container_device.via_device_id == dashy_stack_device.id

    compose_container_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{mock_config_entry.entry_id}_1_serene_banach")}
    )
    assert compose_container_device is not None
    assert compose_container_device.via_device_id == webstack_device.id

    standalone_container_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{mock_config_entry.entry_id}_1_focused_einstein")}
    )

    assert standalone_container_device is not None
    assert standalone_container_device.via_device_id == endpoint_device.id