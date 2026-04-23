async def test_user_sets_unique_id(hass: HomeAssistant) -> None:
    """Test that the user flow sets the unique id."""
    service_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.43.183"),
        ip_addresses=[ip_address("192.168.43.183")],
        hostname="test8266.local.",
        name="mock_name",
        port=6053,
        properties={
            "mac": "1122334455aa",
        },
        type="mock_type",
    )
    discovery_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=service_info
    )

    assert discovery_result["type"] is FlowResultType.FORM
    assert discovery_result["step_id"] == "discovery_confirm"
    assert discovery_result["description_placeholders"] == {
        "name": "test8266",
    }

    discovery_result = await hass.config_entries.flow.async_configure(
        discovery_result["flow_id"],
        {},
    )
    assert discovery_result["type"] is FlowResultType.CREATE_ENTRY
    assert discovery_result["data"] == {
        CONF_HOST: "192.168.43.183",
        CONF_PORT: 6053,
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: "",
        CONF_DEVICE_NAME: "test",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=None,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "127.0.0.1", CONF_PORT: 6053},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured_updates"
    assert result["description_placeholders"] == {
        "title": "test",
        "name": "test",
        "mac": "11:22:33:44:55:aa",
    }