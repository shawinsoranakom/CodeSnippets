async def test_config_flow(
    hass: HomeAssistant,
) -> None:
    """Test the complete config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    assert result["data"] == {
        "host": HOMEE_IP,
        "username": TESTUSER,
        "password": TESTPASS,
    }
    assert result["title"] == f"{HOMEE_NAME} ({HOMEE_IP})"
    assert result["result"].unique_id == HOMEE_ID