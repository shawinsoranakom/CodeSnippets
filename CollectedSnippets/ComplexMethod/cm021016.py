async def test_hassio_confirm(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we can finish a config flow."""
    aioclient_mock.get(
        "http://mock-adguard:3000/control/status",
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={
                "addon": "AdGuard Home Addon",
                "host": "mock-adguard",
                "port": 3000,
            },
            name="AdGuard Home Addon",
            slug="adguard",
            uuid="1234",
        ),
        context={"source": config_entries.SOURCE_HASSIO},
    )
    assert result
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hassio_confirm"
    assert result["description_placeholders"] == {"addon": "AdGuard Home Addon"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result
    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "AdGuard Home Addon"
    assert config_entry.data == {
        CONF_HOST: "mock-adguard",
        CONF_PASSWORD: None,
        CONF_PORT: 3000,
        CONF_SSL: False,
        CONF_USERNAME: None,
        CONF_VERIFY_SSL: True,
    }