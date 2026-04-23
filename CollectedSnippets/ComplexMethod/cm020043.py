async def test_controller_invalid_auth(
    hass: HomeAssistant,
    mock_setup: Mock,
    responses: list[AiohttpClientMockResponse],
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test an invalid password."""

    responses.clear()
    responses.extend(
        [
            # Incorrect password response
            AiohttpClientMockResponse("POST", URL, status=HTTPStatus.FORBIDDEN),
            # Second attempt with the correct password
            mock_response(MODEL_AND_VERSION_RESPONSE),
            mock_response(SERIAL_RESPONSE),
            mock_json_response(WIFI_PARAMS_RESPONSE),
        ]
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert not result.get("errors")
    assert "flow_id" in result

    # Simulate authentication error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST, CONF_PASSWORD: "wrong-password"},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert result.get("errors") == {"base": "invalid_auth"}

    assert not mock_setup.mock_calls

    # Correct the form and enter the password again and setup completes
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST, CONF_PASSWORD: PASSWORD},
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == HOST
    assert "result" in result
    assert dict(result["result"].data) == CONFIG_ENTRY_DATA
    assert result["result"].unique_id == MAC_ADDRESS_UNIQUE_ID

    assert len(mock_setup.mock_calls) == 1