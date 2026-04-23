async def test_flow_works(hass: HomeAssistant, mock_discovery) -> None:
    """Test config flow."""
    mock_discovery.return_value = "1"
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["data_schema"]({CONF_USERNAME: "", CONF_PASSWORD: ""}) == {
        CONF_HOST: "unifi",
        CONF_USERNAME: "",
        CONF_PASSWORD: "",
        CONF_PORT: 443,
        CONF_VERIFY_SSL: False,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "1.2.3.4",
            CONF_USERNAME: "username",
            CONF_PASSWORD: "password",
            CONF_PORT: 1234,
            CONF_VERIFY_SSL: True,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Site name"
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "username",
        CONF_PASSWORD: "password",
        CONF_PORT: 1234,
        CONF_SITE_ID: "site_id",
        CONF_VERIFY_SSL: True,
    }
    assert result["result"].unique_id == "1"