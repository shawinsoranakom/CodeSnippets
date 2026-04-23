async def test_user_device_exists_abort(hass: HomeAssistant) -> None:
    """Test we abort user flow if Smappee device already configured."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value={}),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_advanced_config",
            return_value=[{"key": "mdnsHostName", "value": "Smappee1006000212"}],
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_command_control_config", return_value=[]
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_instantaneous",
            return_value=[{"key": "phase0ActivePower", "value": 0}],
        ),
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={"host": "1.2.3.4"},
            unique_id="1006000212",
            source=SOURCE_USER,
        )
        config_entry.add_to_hass(hass)
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        assert result["step_id"] == "environment"
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"environment": ENV_LOCAL}
        )
        assert result["step_id"] == ENV_LOCAL
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1