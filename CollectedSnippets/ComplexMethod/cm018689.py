async def test_import_dataset(
    hass: HomeAssistant,
    mock_async_zeroconf: MagicMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test the active dataset is imported at setup."""
    add_service_listener_called = asyncio.Event()

    async def mock_add_service_listener(type_: str, listener: Any):
        add_service_listener_called.set()

    mock_async_zeroconf.async_add_service_listener = AsyncMock(
        side_effect=mock_add_service_listener
    )
    mock_async_zeroconf.async_remove_service_listener = AsyncMock()
    mock_async_zeroconf.async_get_service_info = AsyncMock()

    assert await thread.async_get_preferred_dataset(hass) is None

    config_entry = MockConfigEntry(
        data=CONFIG_ENTRY_DATA_MULTIPAN,
        domain=otbr.DOMAIN,
        options={},
        title="My OTBR",
        unique_id=TEST_BORDER_AGENT_EXTENDED_ADDRESS.hex(),
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.thread.dataset_store.BORDER_AGENT_DISCOVERY_TIMEOUT",
            0.1,
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        # Wait for Thread router discovery to start
        await add_service_listener_called.wait()
        mock_async_zeroconf.async_add_service_listener.assert_called_once_with(
            "_meshcop._udp.local.", ANY
        )

        # Discover a service matching our router
        listener: discovery.ThreadRouterDiscovery.ThreadServiceListener = (
            mock_async_zeroconf.async_add_service_listener.mock_calls[0][1][1]
        )
        mock_async_zeroconf.async_get_service_info.return_value = AsyncServiceInfo(
            **ROUTER_DISCOVERY_HASS
        )
        listener.add_service(
            None, ROUTER_DISCOVERY_HASS["type_"], ROUTER_DISCOVERY_HASS["name"]
        )

        # Wait for discovery of other routers to time out
        await hass.async_block_till_done()

    dataset_store = await thread.dataset_store.async_get_store(hass)
    assert (
        list(dataset_store.datasets.values())[0].preferred_border_agent_id
        == TEST_BORDER_AGENT_ID.hex()
    )
    assert (
        list(dataset_store.datasets.values())[0].preferred_extended_address
        == TEST_BORDER_AGENT_EXTENDED_ADDRESS.hex()
    )
    assert await thread.async_get_preferred_dataset(hass) == DATASET_CH16.hex()
    assert not issue_registry.async_get_issue(
        domain=otbr.DOMAIN, issue_id=f"insecure_thread_network_{config_entry.entry_id}"
    )
    assert not issue_registry.async_get_issue(
        domain=otbr.DOMAIN,
        issue_id=f"otbr_zha_channel_collision_{config_entry.entry_id}",
    )