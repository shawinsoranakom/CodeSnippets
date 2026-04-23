async def test_form_valid_auth(hass: HomeAssistant, user_flow: str) -> None:
    """Test we handle valid auth."""
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
            return_value=True,
        ),
        patch(
            "homeassistant.components.kodi.config_flow.get_kodi_connection",
            return_value=MockConnection(),
        ),
        patch(
            "homeassistant.components.kodi.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_CREDENTIALS
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_HOST["host"]
    assert result["data"] == {
        **TEST_HOST,
        **TEST_WS_PORT,
        **TEST_CREDENTIALS,
        "name": None,
        "timeout": DEFAULT_TIMEOUT,
    }

    assert len(mock_setup_entry.mock_calls) == 1