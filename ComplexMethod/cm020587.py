async def test_user_websocket_auth_retry(hass: HomeAssistant) -> None:
    """Test starting a flow by user for not supported device."""
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote.open",
            side_effect=UnauthorizedError,
        ),
    ):
        # websocket device not supported
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pairing"
    assert result["errors"] == {"base": "auth_missing"}
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote.open",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room (82GXARRS)"
    assert result["data"][CONF_HOST] == "10.20.43.21"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["data"][CONF_MODEL] == "82GXARRS"
    assert result["data"][CONF_PORT] == 8002
    assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"