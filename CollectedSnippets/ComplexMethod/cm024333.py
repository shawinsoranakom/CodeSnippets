async def test_config_entry_fills_unique_id_with_directed_discovery(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test that the unique id is added if its missing via directed (not broadcast) discovery."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: DEVICE_IP_ADDRESS}, unique_id=None
    )
    config_entry.add_to_hass(hass)
    last_address = None

    async def _async_scan(*args, address=None, **kwargs):
        # Only return discovery results when doing directed discovery
        nonlocal last_address
        last_address = address

    @property
    def found_devices(self):
        nonlocal last_address
        return [DEVICE_30303] if last_address == DEVICE_IP_ADDRESS else []

    mock_aio_discovery = MagicMock(auto_spec=AIODiscovery30303)
    mock_aio_discovery.async_scan = _async_scan
    type(mock_aio_discovery).found_devices = found_devices

    with (
        _patch_status(MOCK_ASYNC_GET_STATUS_ACTIVE),
        patch(
            "homeassistant.components.steamist.discovery.AIODiscovery30303",
            return_value=mock_aio_discovery,
        ),
    ):
        await async_setup_component(hass, steamist.DOMAIN, {steamist.DOMAIN: {}})
        await hass.async_block_till_done()
        assert config_entry.state is ConfigEntryState.LOADED

    assert config_entry.unique_id == FORMATTED_MAC_ADDRESS
    assert config_entry.data[CONF_NAME] == DEVICE_NAME
    assert config_entry.title == DEVICE_NAME

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, FORMATTED_MAC_ADDRESS)}
    )
    assert isinstance(device_entry, dr.DeviceEntry)
    assert device_entry.name == DEVICE_NAME
    assert device_entry.model == DEVICE_MODEL