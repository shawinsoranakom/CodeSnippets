async def test_config_flow_unsigned_eula(
    hass: HomeAssistant, my_permobil: Mock
) -> None:
    """Test email code verification with unsigned eula error.

    Test the config flow from start to until email code verification
    and have the API return that the eula is unsigned.
    """
    my_permobil.request_application_token.side_effect = MyPermobilEulaException
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
    # here the request_application_token raises a MyPermobilEulaException
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "email_code"
    assert result["errors"]["base"] == "unsigned_eula"

    # Retry to submit the code again, but this time the user has signed the EULA
    with patch.object(
        my_permobil,
        "request_application_token",
        return_value=MOCK_TOKEN,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CODE: MOCK_CODE},
        )

    # Now the method should not raise an exception, and you can proceed with your assertions
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == VALID_DATA