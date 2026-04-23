async def test_form_cannot_connect_ws(hass: HomeAssistant, user_flow: str) -> None:
    """Test we handle cannot connect over WebSocket error."""
    with (
        patch(
            "homeassistant.components.kodi.config_flow.Kodi.ping",
            return_value=True,
        ),
        patch.object(
            MockWSConnection,
            "connect",
            AsyncMock(side_effect=CannotConnectError),
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            new=get_kodi_connection,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(user_flow, TEST_HOST)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ws_port"
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.kodi.config_flow.Kodi.ping",
            return_value=True,
        ),
        patch.object(
            MockWSConnection, "connected", new_callable=PropertyMock(return_value=False)
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            new=get_kodi_connection,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_WS_PORT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ws_port"
    assert result["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "homeassistant.components.kodi.config_flow.Kodi.ping",
            side_effect=CannotConnectError,
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            new=get_kodi_connection,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_WS_PORT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ws_port"
    assert result["errors"] == {"base": "cannot_connect"}