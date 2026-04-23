async def test_zeroconf_flow_already_configured_host_changed_reloads_entry(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test we abort the zeroconf flow if already configured and reload if host or name changed."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    name_existing = "existing name should change since we prefer one from discovery"
    host_existing = "1.2.3.45"
    assert host_existing != host
    assert name_existing != name

    mock_config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host_existing,
            "name": name_existing,
            "mac": mac,
        },
        unique_id=unique_id,
    )
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(host),
            ip_addresses=[ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={"bt": mac},
        ),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    await hass.async_block_till_done()
    assert mock_config_entry.data == {
        "host": host,
        "name": name,
        "mac": mac,
    }
    assert len(mock_unload_entry.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 2