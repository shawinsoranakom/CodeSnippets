async def test_user_network_succes(
    hass: HomeAssistant, inputParams: str, expected: str
) -> None:
    """Test user network config."""
    # inttial menu show
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result
    assert result.get("flow_id")
    assert result.get("type") is FlowResultType.MENU
    assert result.get("step_id") == "user"
    assert result.get("menu_options") == ["network", "usbselect"]
    # select the network option
    result = await hass.config_entries.flow.async_configure(
        result.get("flow_id"),
        {"next_step_id": "network"},
    )
    assert result["type"] is FlowResultType.FORM
    # fill in the network form
    result = await hass.config_entries.flow.async_configure(
        result.get("flow_id"),
        {
            CONF_HOST: "velbus",
            CONF_PORT: 6000,
            **inputParams,
        },
    )
    assert result
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "vlp"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    data = result.get("data")
    assert data
    assert data[CONF_PORT] == expected