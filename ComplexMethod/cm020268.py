async def test_config_flow_failures(hass: HomeAssistant) -> None:
    """Test config flow with failures."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    test_data = {
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
    }
    with patch(
        "pyipma.location.Location.get",
        side_effect=IPMAException(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            test_data,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}
    with patch(
        "pyipma.location.Location.get",
        return_value=MockLocation(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            test_data,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "HomeTown"
    assert result["data"] == {
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
    }