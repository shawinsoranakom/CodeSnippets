async def test_full_zeroconf_flow_next_generation(hass: HomeAssistant) -> None:
    """Test the full zeroconf flow."""
    with (
        patch("pysmappee.mqtt.SmappeeLocalMqtt.start_attempt", return_value=True),
        patch(
            "pysmappee.mqtt.SmappeeLocalMqtt.start",
            return_value=None,
        ),
        patch(
            "pysmappee.mqtt.SmappeeLocalMqtt.is_config_ready",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=22,
                hostname="Smappee5001000212.local.",
                type="_ssh._tcp.local.",
                name="Smappee5001000212._ssh._tcp.local.",
                properties={"_raw": {}},
            ),
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zeroconf_confirm"
        assert result["description_placeholders"] == {CONF_SERIALNUMBER: "5001000212"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "smappee5001000212"
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        assert entry.unique_id == "5001000212"