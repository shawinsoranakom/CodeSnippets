async def test_user_legacy_does_not_ok_first_time(hass: HomeAssistant) -> None:
    """Test starting a flow by user."""
    # show form
    with patch(
        "homeassistant.components.samsungtv.bridge.Remote",
        side_effect=AccessDenied("Boom"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        # entry was added
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    with patch("homeassistant.components.samsungtv.bridge.Remote"):
        # entry was added
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], user_input={}
        )

    # legacy tv entry created
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "10.20.43.21"
    assert result3["data"][CONF_HOST] == "10.20.43.21"
    assert result3["data"][CONF_METHOD] == METHOD_LEGACY
    assert result3["data"][CONF_MANUFACTURER] == DEFAULT_MANUFACTURER
    assert result3["data"][CONF_MODEL] is None
    assert result3["data"][CONF_PORT] == 55000
    assert result3["result"].unique_id is None