async def test_form_invalid_auth(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    caplog.set_level(logging.DEBUG)

    api_auth_error_unknown = HTTPError("unknown error")
    with patch(
        "coinbase.rest.RESTClient.get_portfolios",
        side_effect=api_auth_error_unknown,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "123456",
                CONF_API_TOKEN: "AbCDeF",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}
    assert "Coinbase rejected API credentials due to an unknown error" in caplog.text

    api_auth_error_key = HTTPError("invalid api key")
    with patch(
        "coinbase.rest.RESTClient.get_portfolios",
        side_effect=api_auth_error_key,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "123456",
                CONF_API_TOKEN: "AbCDeF",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth_key"}
    assert "Coinbase rejected API credentials due to an invalid API key" in caplog.text

    api_auth_error_secret = HTTPError("invalid signature")
    with patch(
        "coinbase.rest.RESTClient.get_portfolios",
        side_effect=api_auth_error_secret,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "123456",
                CONF_API_TOKEN: "AbCDeF",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth_secret"}
    assert (
        "Coinbase rejected API credentials due to an invalid API secret" in caplog.text
    )