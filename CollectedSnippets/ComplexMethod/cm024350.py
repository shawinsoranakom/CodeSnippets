async def test_form_invalid_auth(hass: HomeAssistant, user_flow: str) -> None:
    """Test we handle invalid auth."""
    with (
        patch(
            "homeassistant.components.kodi.config_flow.Kodi.ping",
            side_effect=InvalidAuthError,
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            return_value=MockConnection(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(user_flow, TEST_HOST)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.kodi.config_flow.Kodi.ping",
            side_effect=InvalidAuthError,
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            return_value=MockConnection(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_CREDENTIALS
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {"base": "invalid_auth"}

    with (
        patch(
            "homeassistant.components.kodi.config_flow.Kodi.ping",
            side_effect=CannotConnectError,
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            return_value=MockConnection(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_CREDENTIALS
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "homeassistant.components.kodi.config_flow.Kodi.ping",
            side_effect=Exception,
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            return_value=MockConnection(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_CREDENTIALS
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {"base": "unknown"}

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
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_CREDENTIALS
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ws_port"
    assert result["errors"] == {}