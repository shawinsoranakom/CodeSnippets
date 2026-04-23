async def test_cloud_abort_on_duplicate_entry(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the form."""

    MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD, "hub": TEST_SERVER},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM

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

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"