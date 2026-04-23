async def test_local_zeroconf_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test that zeroconf discovery for new local bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=FAKE_ZERO_CONF_INFO_LOCAL,
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
        {"api_type": "local"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "local"

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "gateway-1234-5678-9123.local:8443",
                "token": TEST_TOKEN,
                "verify_ssl": False,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "gateway-1234-5678-9123.local:8443"

    # Verify no username/password in data
    assert result["data"] == {
        "host": "gateway-1234-5678-9123.local:8443",
        "token": TEST_TOKEN,
        "verify_ssl": False,
        "hub": TEST_SERVER,
        "api_type": "local",
    }
    assert len(mock_setup_entry.mock_calls) == 1