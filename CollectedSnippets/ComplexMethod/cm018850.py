async def test_user_flow_error(
    hass: HomeAssistant,
    side_effect,
    expected_error,
    get_client: AirPatrolAPI,
) -> None:
    """Test user flow with invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.airpatrol.config_flow.AirPatrolAPI.authenticate",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_USER_INPUT
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": expected_error}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_USER_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_USER_INPUT[CONF_EMAIL]
    assert result["data"] == {
        **TEST_USER_INPUT,
        CONF_ACCESS_TOKEN: "test_access_token",
    }
    assert result["result"].unique_id == "test_user_id"