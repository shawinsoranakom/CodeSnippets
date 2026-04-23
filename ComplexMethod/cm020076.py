async def test_climate_on_off(
    hass: HomeAssistant, knx: KNXTestKit, heat_cool_ga: str | None
) -> None:
    """Test KNX climate on/off."""
    on_off_ga = "3/3/3"
    await knx.setup_integration(
        {
            ClimateSchema.PLATFORM: {
                CONF_NAME: "test",
                ClimateSchema.CONF_TEMPERATURE_ADDRESS: "1/2/3",
                ClimateSchema.CONF_TARGET_TEMPERATURE_ADDRESS: "1/2/4",
                ClimateSchema.CONF_TARGET_TEMPERATURE_STATE_ADDRESS: "1/2/5",
                ClimateSchema.CONF_ON_OFF_ADDRESS: on_off_ga,
                ClimateSchema.CONF_ON_OFF_STATE_ADDRESS: "1/2/9",
            }
            | (
                {
                    ClimateSchema.CONF_HEAT_COOL_ADDRESS: heat_cool_ga,
                    ClimateSchema.CONF_HEAT_COOL_STATE_ADDRESS: "1/2/11",
                }
                if heat_cool_ga
                else {}
            )
        }
    )
    # read temperature state
    await knx.assert_read("1/2/3")
    await knx.receive_response("1/2/3", RAW_FLOAT_20_0)
    # read target temperature state
    await knx.assert_read("1/2/5")
    await knx.receive_response("1/2/5", RAW_FLOAT_22_0)
    # read on/off state
    await knx.assert_read("1/2/9")
    await knx.receive_response("1/2/9", 1)
    # read heat/cool state
    if heat_cool_ga:
        await knx.assert_read("1/2/11")
        await knx.receive_response("1/2/11", 0)  # cool

    # turn off
    await hass.services.async_call(
        "climate",
        "turn_off",
        {"entity_id": "climate.test"},
        blocking=True,
    )
    await knx.assert_write(on_off_ga, 0)
    assert hass.states.get("climate.test").state == "off"

    # turn on
    await hass.services.async_call(
        "climate",
        "turn_on",
        {"entity_id": "climate.test"},
        blocking=True,
    )
    await knx.assert_write(on_off_ga, 1)
    if heat_cool_ga:
        # does not fall back to default hvac mode after turn_on
        assert hass.states.get("climate.test").state == "cool"
    else:
        assert hass.states.get("climate.test").state == "heat"

    # set hvac mode to off triggers turn_off if no controller_mode is available
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.test", "hvac_mode": HVACMode.OFF},
        blocking=True,
    )
    await knx.assert_write(on_off_ga, 0)
    assert hass.states.get("climate.test").state == "off"

    # set hvac mode to heat
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.test", "hvac_mode": HVACMode.HEAT},
        blocking=True,
    )
    if heat_cool_ga:
        await knx.assert_write(heat_cool_ga, 1)
        await knx.assert_write(on_off_ga, 1)
    else:
        await knx.assert_write(on_off_ga, 1)
    assert hass.states.get("climate.test").state == "heat"