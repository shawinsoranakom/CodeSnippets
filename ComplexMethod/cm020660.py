async def test_happy_flow(hass: HomeAssistant) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert len(result["data_schema"].schema[CONF_STATION_ID].config["options"]) == 2

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home"
    assert result["data"] == {
        CONF_STATION_ID: 123,
        CONF_NAME: "Home",
    }

    assert result["result"].unique_id == "123"