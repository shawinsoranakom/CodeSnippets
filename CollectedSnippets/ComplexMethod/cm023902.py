async def test_create_entry(hass: HomeAssistant, use_psk, use_ssl) -> None:
    """Test that entry is added correctly."""
    uuid = await instance_id.async_get(hass)

    with (
        patch("pybravia.BraviaClient.connect"),
        patch("pybravia.BraviaClient.pair"),
        patch("pybravia.BraviaClient.set_wol_mode"),
        patch(
            "pybravia.BraviaClient.get_system_info",
            return_value=BRAVIA_SYSTEM_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "authorize"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: use_psk, CONF_USE_SSL: use_ssl}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "psk" if use_psk else "pin"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "secret"}
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].unique_id == "very_unique_string"
        assert result["title"] == "BRAVIA TV-Model"
        assert result["data"] == {
            CONF_HOST: "bravia-host",
            CONF_PIN: "secret",
            CONF_USE_PSK: use_psk,
            CONF_USE_SSL: use_ssl,
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            **(
                {
                    CONF_CLIENT_ID: uuid,
                    CONF_NICKNAME: f"{NICKNAME_PREFIX} {uuid[:6]}",
                }
                if not use_psk
                else {}
            ),
        }