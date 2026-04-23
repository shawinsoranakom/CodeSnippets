async def test_user_flow_already_configured_host_changed_reloads_entry(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test we abort the user flow if already configured and reload if host changed."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    name_existing = "existing name if different is from discovery and should not change"
    host_existing = "1.2.3.45"
    assert host_existing != host

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
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "host" in result["data_schema"].schema
    assert not result["errors"]

    mock_api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    mock_api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "already_configured"

    mock_api.async_generate_cert_if_missing.assert_called()
    mock_api.async_get_name_and_mac.assert_called()
    mock_api.async_start_pairing.assert_not_called()

    await hass.async_block_till_done()
    assert len(mock_unload_entry.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 2
    assert mock_config_entry.data == {
        "host": host,
        "name": name_existing,
        "mac": mac,
    }