async def test_hvac_mode_change_user_context(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    """Test user context is preserved through the full chain.

    Full chain:
    1. User calls set_hvac_mode → parent context (has user_id)
    2. Generic thermostat calls homeassistant.turn_on → child context (no user_id)
    3. Switch state changes → child context
    4. Climate state updates in response → child context
    """
    heater_switch = "input_boolean.test"
    assert await async_setup_component(
        hass, input_boolean.DOMAIN, {"input_boolean": {"test": None}}
    )

    assert await async_setup_component(
        hass,
        CLIMATE_DOMAIN,
        {
            "climate": {
                "platform": "generic_thermostat",
                "name": "test",
                "heater": heater_switch,
                "target_sensor": ENT_SENSOR,
                "initial_hvac_mode": HVACMode.OFF,
                "cold_tolerance": 2,
                "hot_tolerance": 4,
            }
        },
    )
    await hass.async_block_till_done()

    # Set sensor below target so heating triggers on mode change
    _setup_sensor(hass, 18)
    await hass.async_block_till_done()
    await common.async_set_temperature(hass, 23)
    await hass.async_block_till_done()

    assert hass.states.get(heater_switch).state == STATE_OFF

    # Change HVAC mode with a user context
    user_context = Context(user_id=hass_admin_user.id)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {"entity_id": ENTITY, "hvac_mode": HVACMode.HEAT},
        blocking=True,
        context=user_context,
    )
    await hass.async_block_till_done()

    # Step 2: The heater should have been turned on
    assert hass.states.get(heater_switch).state == STATE_ON

    # The switch state change should have a child context with the
    # user context as parent
    switch_state = hass.states.get(heater_switch)
    child_context = switch_state.context
    assert child_context.id != user_context.id
    assert child_context.parent_id == user_context.id

    # Step 4: The climate entity should keep the parent (user) context,
    # not the child context created for the switch service call
    climate_state = hass.states.get(ENTITY)
    assert climate_state.context.id == user_context.id
    assert climate_state.context.user_id == hass_admin_user.id