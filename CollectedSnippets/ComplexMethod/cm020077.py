async def test_climate_hvac_mode(
    hass: HomeAssistant, knx: KNXTestKit, on_off_ga: str | None
) -> None:
    """Test KNX climate hvac mode."""
    controller_mode_ga = "3/3/3"
    await knx.setup_integration(
        {
            ClimateSchema.PLATFORM: {
                CONF_NAME: "test",
                ClimateSchema.CONF_TEMPERATURE_ADDRESS: "1/2/3",
                ClimateSchema.CONF_TARGET_TEMPERATURE_ADDRESS: "1/2/4",
                ClimateSchema.CONF_TARGET_TEMPERATURE_STATE_ADDRESS: "1/2/5",
                ClimateSchema.CONF_CONTROLLER_MODE_ADDRESS: controller_mode_ga,
                ClimateSchema.CONF_CONTROLLER_MODE_STATE_ADDRESS: "1/2/7",
                ClimateConf.OPERATION_MODES: ["Auto"],
            }
            | (
                {
                    ClimateSchema.CONF_ON_OFF_ADDRESS: on_off_ga,
                }
                if on_off_ga
                else {}
            )
        }
    )
    # read states state updater
    # StateUpdater semaphore allows 2 concurrent requests
    await knx.assert_read("1/2/3")
    await knx.assert_read("1/2/5")
    # StateUpdater initialize state
    await knx.receive_response("1/2/3", RAW_FLOAT_20_0)
    await knx.receive_response("1/2/5", RAW_FLOAT_22_0)
    await knx.assert_read("1/2/7")
    await knx.receive_response("1/2/7", (0x01,))

    # turn hvac mode to off - set_hvac_mode() doesn't send to on_off if dedicated hvac mode is available
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.test", "hvac_mode": HVACMode.OFF},
        blocking=True,
    )
    await knx.assert_write(controller_mode_ga, (0x06,))
    if on_off_ga:
        await knx.assert_write(on_off_ga, 0)
    assert hass.states.get("climate.test").state == "off"

    # set hvac to non default mode
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.test", "hvac_mode": HVACMode.COOL},
        blocking=True,
    )
    await knx.assert_write(controller_mode_ga, (0x03,))
    if on_off_ga:
        await knx.assert_write(on_off_ga, 1)
    assert hass.states.get("climate.test").state == "cool"

    # turn off
    await hass.services.async_call(
        "climate",
        "turn_off",
        {"entity_id": "climate.test"},
        blocking=True,
    )
    if on_off_ga:
        await knx.assert_write(on_off_ga, 0)
    else:
        await knx.assert_write(controller_mode_ga, (0x06,))
    assert hass.states.get("climate.test").state == "off"

    # turn on
    await hass.services.async_call(
        "climate",
        "turn_on",
        {"entity_id": "climate.test"},
        blocking=True,
    )
    if on_off_ga:
        await knx.assert_write(on_off_ga, 1)
    else:
        # restore last hvac mode
        await knx.assert_write(controller_mode_ga, (0x03,))
    assert hass.states.get("climate.test").state == "cool"