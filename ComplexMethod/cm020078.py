async def test_climate_heat_cool_read_only_on_off(
    hass: HomeAssistant, knx: KNXTestKit
) -> None:
    """Test KNX climate hvac mode."""
    on_off_ga = "2/2/2"
    heat_cool_state_ga = "3/3/3"
    await knx.setup_integration(
        {
            ClimateSchema.PLATFORM: {
                CONF_NAME: "test",
                ClimateSchema.CONF_TEMPERATURE_ADDRESS: "1/2/3",
                ClimateSchema.CONF_TARGET_TEMPERATURE_ADDRESS: "1/2/4",
                ClimateSchema.CONF_TARGET_TEMPERATURE_STATE_ADDRESS: "1/2/5",
                ClimateSchema.CONF_ON_OFF_ADDRESS: on_off_ga,
                ClimateSchema.CONF_HEAT_COOL_STATE_ADDRESS: heat_cool_state_ga,
            }
        }
    )
    # read states state updater
    # StateUpdater semaphore allows 2 concurrent requests
    await knx.assert_read("1/2/3")
    await knx.assert_read("1/2/5")
    # StateUpdater initialize state
    await knx.receive_response("1/2/3", RAW_FLOAT_20_0)
    await knx.receive_response("1/2/5", RAW_FLOAT_20_0)
    await knx.assert_read(heat_cool_state_ga)
    await knx.receive_response(heat_cool_state_ga, True)  # heat

    state = hass.states.get("climate.test")
    assert state.state == "off"
    assert set(state.attributes["hvac_modes"]) == {"off", "heat"}
    assert state.attributes["hvac_action"] == "off"

    await knx.receive_write(heat_cool_state_ga, False)  # cool
    state = hass.states.get("climate.test")
    assert state.state == "off"
    assert set(state.attributes["hvac_modes"]) == {"off", "cool"}
    assert state.attributes["hvac_action"] == "off"

    await knx.receive_write(on_off_ga, True)
    state = hass.states.get("climate.test")
    assert state.state == "cool"
    assert set(state.attributes["hvac_modes"]) == {"off", "cool"}
    assert state.attributes["hvac_action"] == "cooling"