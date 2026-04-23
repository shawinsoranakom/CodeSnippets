async def test_dhcp_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test that DHCP discovery for new bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(
            hostname="gateway-1234-5678-9123",
            ip="192.168.1.4",
            macaddress="f8811a000000",
        ),
        context={"source": config_entries.SOURCE_DHCP},
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

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch("pyoverkiz.client.OverkizClient.get_gateways", return_value=None),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
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