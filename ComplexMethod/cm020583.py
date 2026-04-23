async def test_user_legacy(hass: HomeAssistant) -> None:
    """Test starting a flow by user."""
    # show form
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Wrong host allow to retry
    with patch(
        "homeassistant.components.samsungtv.config_flow.socket.gethostbyname",
        side_effect=socket.gaierror("[Error -2] Name or Service not known"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_host"}

    # Good host creates entry
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_DATA
    )
    # legacy tv entry created
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.20.43.21"
    assert result["data"][CONF_HOST] == "10.20.43.21"
    assert result["data"][CONF_METHOD] == METHOD_LEGACY
    assert result["data"][CONF_MANUFACTURER] == DEFAULT_MANUFACTURER
    assert result["data"][CONF_MODEL] is None
    assert result["data"][CONF_PORT] == 55000
    assert result["result"].unique_id is None