async def test_connection_aborted_wrong_device(
    hass: HomeAssistant,
    mock_client: APIClient,
    caplog: pytest.LogCaptureFixture,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test we abort the connection if the unique id is a mac and neither name or mac match."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.43.183",
            CONF_PORT: 6053,
            CONF_PASSWORD: "",
            CONF_DEVICE_NAME: "test",
        },
        unique_id="11:22:33:44:55:aa",
    )
    entry.add_to_hass(hass)
    disconnect_done = hass.loop.create_future()

    async def async_disconnect(*args, **kwargs) -> None:
        disconnect_done.set_result(None)

    mock_client.disconnect = async_disconnect
    device_info = DeviceInfo(mac_address="1122334455ab", name="different")
    mock_client.device_info = AsyncMock(return_value=device_info)
    mock_client.list_entities_services = AsyncMock(return_value=([], []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device_info, [], [])
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    async with asyncio.timeout(1):
        await disconnect_done

    assert (
        "Unexpected device found at 192.168.43.183; expected `test` "
        "with mac address `11:22:33:44:55:aa`, found `different` "
        "with mac address `11:22:33:44:55:ab`" in caplog.text
    )
    # If its a different name, it means their DHCP
    # reservations are missing and the device is not
    # actually the same device, and there is nothing
    # we can do to fix it so we only log a warning
    assert not issue_registry.async_get_issue(
        domain=DOMAIN, issue_id=DEVICE_CONFLICT_ISSUE_FORMAT.format(entry.entry_id)
    )

    assert "Error getting setting up connection for" not in caplog.text
    mock_client.disconnect = AsyncMock()
    caplog.clear()
    # Make sure discovery triggers a reconnect
    service_info = DhcpServiceInfo(
        ip="192.168.43.184",
        hostname="test",
        macaddress="1122334455aa",
    )
    device_info = DeviceInfo(mac_address="1122334455aa", name="test")
    new_info = AsyncMock(return_value=device_info)
    mock_client.device_info = new_info
    # Also need to update device_info_and_list_entities
    new_combined_info = AsyncMock(return_value=(device_info, [], []))
    mock_client.device_info_and_list_entities = new_combined_info
    result = await hass.config_entries.flow.async_init(
        "esphome", context={"source": config_entries.SOURCE_DHCP}, data=service_info
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured_updates"
    assert result["description_placeholders"] == {
        "title": "Mock Title",
        "name": "test",
        "mac": "11:22:33:44:55:aa",
    }
    assert entry.data[CONF_HOST] == "192.168.43.184"
    await hass.async_block_till_done()
    # Check that either device_info or device_info_and_list_entities was called
    assert len(new_info.mock_calls) + len(new_combined_info.mock_calls) == 2
    assert "Unexpected device found at" not in caplog.text