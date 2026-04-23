async def test_config_flow_with_region(
    hass: HomeAssistant,
) -> None:
    """Handle the config flow with a specific region."""
    with patch(
        "homeassistant.components.roborock.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        with patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient"
        ) as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.request_code_v4 = AsyncMock(return_value=None)
            mock_client.code_login_v4 = AsyncMock(return_value=USER_DATA)

            # base_url is awaited in config_flow, so it needs to be an awaitable
            future_base_url = asyncio.Future()
            future_base_url.set_result("https://usiot.roborock.com")
            mock_client.base_url = future_base_url

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_USERNAME: USER_EMAIL, CONF_REGION: "us"}
            )

            # Check that the client was initialized with the correct base_url
            mock_client_cls.assert_called_with(
                USER_EMAIL,
                base_url="https://usiot.roborock.com",
                session=async_get_clientsession(hass),
            )

            assert result["type"] is FlowResultType.FORM
            assert result["step_id"] == "code"
            assert result["errors"] == {}

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={CONF_ENTRY_CODE: "123456"}
            )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["context"]["unique_id"] == ROBOROCK_RRUID
    assert result["title"] == USER_EMAIL
    assert result["data"][CONF_BASE_URL] == "https://usiot.roborock.com"
    assert result["result"]
    assert len(mock_setup.mock_calls) == 1