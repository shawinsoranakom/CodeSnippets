async def test_user_incomplete_info(hass: HomeAssistant, service) -> None:
    """Test user step with incomplete device info."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    router_infos = ROUTER_INFOS.copy()
    router_infos.pop("DeviceName")
    service.return_value.get_info = Mock(return_value=router_infos)

    # Have to provide all config
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == TITLE_INCOMPLETE
    assert result["data"].get(CONF_HOST) == HOST
    assert result["data"].get(CONF_PORT) == PORT
    assert result["data"].get(CONF_SSL) == SSL
    assert result["data"].get(CONF_USERNAME) == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD