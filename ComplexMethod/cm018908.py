async def test_cloud_allow_multiple_unique_entries(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the form."""

    MockConfigEntry(
        version=1,
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID2,
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

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_EMAIL
    assert result["data"] == {
        "api_type": "cloud",
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "hub": TEST_SERVER,
    }