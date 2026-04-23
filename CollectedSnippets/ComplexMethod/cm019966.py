async def test_sucessful_config_flow(hass: HomeAssistant, my_permobil: Mock) -> None:
    """Test the config flow from start to finish with no errors."""
    # init flow
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "region"
    assert result["errors"] == {}

    # select region step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: MOCK_REGION_NAME},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "email_code"
    assert result["errors"] == {}
    # request region code
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == VALID_DATA