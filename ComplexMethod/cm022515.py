async def test_zeroconf_flow(hass: HomeAssistant) -> None:
    """Test the zeroconf happy flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="pblr-0000645.local.",
            name="mock_name",
            properties={
                "sn": "23-45-A4O-MOF",
                "version": "1.6.1+1+WL-1",
            },
            type="mock_type",
        ),
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] is FlowResultType.FORM

    progress = hass.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0].get("flow_id") == result["flow_id"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "OMGPINEAPPLES"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "23-45-A4O-MOF"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_PASSWORD: "OMGPINEAPPLES",
    }
    assert not config_entry.options