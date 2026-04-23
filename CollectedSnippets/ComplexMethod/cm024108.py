async def test_discovery_flow(
    hass: HomeAssistant,
    source: str,
    discovery_info: BaseServiceInfo,
) -> None:
    """Test the different discovery flows for new devices work."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, data=discovery_info, context={"source": source}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0].get("context", {}).get("configuration_url") == "http://1.2.3.4:80"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PROTOCOL: "http",
            CONF_HOST: "1.2.3.4",
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pass",
            CONF_PORT: 80,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"M1065-LW - {MAC}"
    assert result["data"] == {
        CONF_PROTOCOL: "http",
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pass",
        CONF_PORT: 80,
        CONF_MODEL: "M1065-LW",
        CONF_NAME: "M1065-LW 0",
    }

    assert result["data"][CONF_NAME] == "M1065-LW 0"