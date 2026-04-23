async def test_zeroconf_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test that zeroconf discovery for new bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=FAKE_ZERO_CONF_INFO,
        context={"source": config_entries.SOURCE_ZEROCONF},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == config_entries.SOURCE_USER

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "local_or_cloud"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud"

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_EMAIL
    assert result["data"] == {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "hub": TEST_SERVER,
        "api_type": "cloud",
    }

    assert len(mock_setup_entry.mock_calls) == 1