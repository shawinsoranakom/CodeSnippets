async def test_user_flow_pairing_connection_closed_followed_by_cannot_connect(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test async_finish_pairing raises ConnectionClosed and then async_start_pairing raises CannotConnect.

    This is when the user unplugs the Android TV before calling async_finish_pairing.
    We call async_start_pairing again which fails with CannotConnect so we abort.
    """
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
    pin = "123456"

    mock_api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    mock_api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    mock_api.async_start_pairing = AsyncMock(side_effect=[None, CannotConnect()])

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert "pin" in result["data_schema"].schema
    assert not result["errors"]

    mock_api.async_generate_cert_if_missing.assert_called()
    mock_api.async_start_pairing.assert_called()

    mock_api.async_finish_pairing = AsyncMock(side_effect=ConnectionClosed())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"

    mock_api.async_finish_pairing.assert_called_with(pin)

    assert mock_api.async_get_name_and_mac.call_count == 1
    assert mock_api.async_start_pairing.call_count == 2
    assert mock_api.async_finish_pairing.call_count == 1

    await hass.async_block_till_done()
    assert len(mock_unload_entry.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0