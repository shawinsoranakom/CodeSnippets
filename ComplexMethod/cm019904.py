async def test_user_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test the full user flow from start to finish without any exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "host" in result["data_schema"].schema
    assert not result["errors"]

    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    mock_api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    mock_api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    mock_api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert "pin" in result["data_schema"].schema
    assert not result["errors"]

    mock_api.async_generate_cert_if_missing.assert_called()
    mock_api.async_start_pairing.assert_called()

    mock_api.async_finish_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == name
    assert result["data"] == {"host": host, "name": name, "mac": mac}
    assert result["context"]["source"] == "user"
    assert result["context"]["unique_id"] == unique_id

    mock_api.async_finish_pairing.assert_called_with(pin)

    await hass.async_block_till_done()
    assert len(mock_unload_entry.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 1