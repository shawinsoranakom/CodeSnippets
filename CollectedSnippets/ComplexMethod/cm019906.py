async def test_user_flow_start_pair_cannot_connect(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test async_start_pairing raises CannotConnect in the user flow."""
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

    mock_api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    mock_api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    mock_api.async_start_pairing = AsyncMock(side_effect=CannotConnect())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "host" in result["data_schema"].schema
    assert result["errors"] == {"base": "cannot_connect"}

    mock_api.async_generate_cert_if_missing.assert_called()
    mock_api.async_get_name_and_mac.assert_called()
    mock_api.async_start_pairing.assert_called()

    pin = "123456"
    mock_api.async_start_pairing = AsyncMock(return_value=None)
    mock_api.async_finish_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1