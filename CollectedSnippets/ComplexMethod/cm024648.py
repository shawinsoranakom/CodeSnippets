async def test_auth_create_token_success(hass: HomeAssistant) -> None:
    """Verify correct behaviour when a token is successfully created."""
    result = await _init_flow(hass)

    client = create_mock_client()
    client.async_is_auth_required = AsyncMock(return_value=TEST_AUTH_REQUIRED_RESP)

    with patch(
        "homeassistant.components.hyperion.client.HyperionClient", return_value=client
    ):
        result = await _configure_flow(hass, result, user_input=TEST_HOST_PORT)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"

    client.async_request_token = AsyncMock(return_value=TEST_REQUEST_TOKEN_SUCCESS)
    with (
        patch(
            "homeassistant.components.hyperion.client.HyperionClient",
            return_value=client,
        ),
        patch(
            "homeassistant.components.hyperion.config_flow.client.generate_random_auth_id",
            return_value=TEST_AUTH_ID,
        ),
    ):
        result = await _configure_flow(
            hass, result, user_input={CONF_CREATE_TOKEN: True}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "create_token"
        assert result["description_placeholders"] == {
            CONF_AUTH_ID: TEST_AUTH_ID,
        }

        result = await _configure_flow(hass, result)
        assert result["type"] is FlowResultType.EXTERNAL_STEP
        assert result["step_id"] == "create_token_external"

        # The flow will be automatically advanced by the auth token response.
        result = await _configure_flow(hass, result)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["handler"] == DOMAIN
        assert result["title"] == TEST_TITLE
        assert result["data"] == {
            **TEST_HOST_PORT,
            CONF_TOKEN: TEST_TOKEN,
        }