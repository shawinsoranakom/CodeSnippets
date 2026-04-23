async def test_invalid_session_id(hass: HomeAssistant) -> None:
    """Test Invalid Session ID."""
    with _patch_lg_netcast(session_error=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "authorize"
        assert not result["errors"]

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ACCESS_TOKEN: FAKE_PIN}
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "authorize"
        assert result2["errors"] is not None
        assert result2["errors"]["base"] == "cannot_connect"