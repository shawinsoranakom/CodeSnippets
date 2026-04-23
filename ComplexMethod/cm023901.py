async def test_ssdp_discovery(hass: HomeAssistant) -> None:
    """Test that the device is discovered."""
    uuid = await instance_id.async_get(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=BRAVIA_SSDP,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    with (
        patch("pybravia.BraviaClient.connect"),
        patch("pybravia.BraviaClient.pair"),
        patch("pybravia.BraviaClient.set_wol_mode"),
        patch(
            "pybravia.BraviaClient.get_system_info",
            return_value=BRAVIA_SYSTEM_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "authorize"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: False, CONF_USE_SSL: False}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "pin"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].unique_id == "very_unique_string"
        assert result["title"] == "BRAVIA TV-Model"
        assert result["data"] == {
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_USE_PSK: False,
            CONF_USE_SSL: False,
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_CLIENT_ID: uuid,
            CONF_NICKNAME: f"{NICKNAME_PREFIX} {uuid[:6]}",
        }