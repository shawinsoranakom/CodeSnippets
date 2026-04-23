async def test_setup_v2(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_client: MagicMock,
    config_base: dict[str, Any],
    get_write_api: Any,
) -> None:
    """Test we can setup an InfluxDB v2."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "configure_v2"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_v2"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        config_base,
    )

    data = {
        CONF_API_VERSION: "2",
        CONF_URL: config_base[CONF_URL],
        CONF_ORG: config_base[CONF_ORG],
        CONF_BUCKET: config_base.get(CONF_BUCKET),
        CONF_TOKEN: config_base.get(CONF_TOKEN),
        CONF_VERIFY_SSL: config_base[CONF_VERIFY_SSL],
    }

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{config_base['bucket']} ({config_base['url']})"
    assert result["data"] == data