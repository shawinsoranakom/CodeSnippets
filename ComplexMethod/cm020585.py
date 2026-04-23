async def test_user_websocket(hass: HomeAssistant) -> None:
    """Test starting a flow by user."""
    with patch(
        "homeassistant.components.samsungtv.bridge.Remote", side_effect=OSError("Boom")
    ):
        # show form
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        # entry was added
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )
        # websocket tv entry created
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Living Room (82GXARRS)"
        assert result["data"][CONF_HOST] == "10.20.43.21"
        assert result["data"][CONF_METHOD] == "websocket"
        assert result["data"][CONF_MANUFACTURER] == "Samsung"
        assert result["data"][CONF_MODEL] == "82GXARRS"
        assert result["data"][CONF_PORT] == 8002
        assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"