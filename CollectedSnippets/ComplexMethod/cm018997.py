async def test_zeroconf(hass: HomeAssistant) -> None:
    """Test that the zeroconf form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["description_placeholders"] == {"host_name": "test"}

    context = next(
        flow["context"]
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )

    assert (
        context["title_placeholders"][CONF_NAME]
        == DISCOVERY_INFO.hostname.split(".", maxsplit=1)[0]
    )

    with (
        patch(
            "homeassistant.components.devolo_home_network.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.devolo_home_network.config_flow.Device",
            new=MockDevice,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["title"] == "test"
    assert result2["data"] == {
        CONF_IP_ADDRESS: IP,
        CONF_PASSWORD: "",
    }
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["result"].unique_id == "1234567890"