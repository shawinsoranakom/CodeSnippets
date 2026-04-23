async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "CPU Temperature rising", "entity_id": "sensor.cpu_temp"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM

    # test step 2 of config flow: settings of trend sensor
    with patch(
        "homeassistant.components.trend.async_setup_entry", wraps=async_setup_entry
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "invert": False,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "CPU Temperature rising"
    assert result["data"] == {}
    assert result["options"] == {
        "entity_id": "sensor.cpu_temp",
        "invert": False,
        "name": "CPU Temperature rising",
    }