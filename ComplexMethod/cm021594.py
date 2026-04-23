async def test_reauth_connection_error(hass: HomeAssistant) -> None:
    """Test we show user form on connection error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=FIXTURE_UUID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "authenticate"

    with patch(
        "systembridgeconnector.websocket_client.WebSocketClient.connect",
        side_effect=ConnectionErrorException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "authenticate"
    assert result2["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.connect",
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            return_value=None,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "authenticate"
    assert result3["errors"] == {"base": "cannot_connect"}