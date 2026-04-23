async def test_setup_v1(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_client: MagicMock,
    config_base: dict[str, Any],
    config_url: dict[str, Any],
    get_write_api: Any,
) -> None:
    """Test we can setup an InfluxDB v1."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "configure_v1"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_v1"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        config_base,
    )

    data = {
        CONF_API_VERSION: "1",
        CONF_HOST: config_url[CONF_HOST],
        CONF_PORT: config_url[CONF_PORT],
        CONF_USERNAME: config_base.get(CONF_USERNAME),
        CONF_PASSWORD: config_base.get(CONF_PASSWORD),
        CONF_DB_NAME: config_base[CONF_DB_NAME],
        CONF_SSL: config_url[CONF_SSL],
        CONF_PATH: config_url[CONF_PATH],
        CONF_VERIFY_SSL: config_base[CONF_VERIFY_SSL],
    }

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{config_base['database']} ({config_url['host']})"
    assert result["data"] == data