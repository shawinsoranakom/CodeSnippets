async def test_user_flow_with_auth(
    hass: HomeAssistant,
    mock_charger: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user flow create entry with authentication."""
    mock_charger.test_and_get.side_effect = [
        AuthenticationError,
        {"serial": "deadbeeffeed"},
    ]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OpenEVSE 10.0.0.131"
    assert result["data"] == {
        CONF_HOST: "10.0.0.131",
        CONF_USERNAME: "fakeuser",
        CONF_PASSWORD: "muchpassword",
    }
    assert result["result"].unique_id == "deadbeeffeed"