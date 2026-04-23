async def test_full_zeroconf_flow(hass: HomeAssistant) -> None:
    """Test the full zeroconf flow."""
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
        patch("homeassistant.components.smappee.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=22,
                hostname="Smappee1006000212.local.",
                type="_ssh._tcp.local.",
                name="Smappee1006000212._ssh._tcp.local.",
                properties={"_raw": {}},
            ),
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zeroconf_confirm"
        assert result["description_placeholders"] == {CONF_SERIALNUMBER: "1006000212"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "smappee1006000212"
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        assert entry.unique_id == "1006000212"