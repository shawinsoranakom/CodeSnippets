async def test_climate(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_legacy: AsyncMock,
) -> None:
    """Tests that the climate entity is correct."""

    entry = await setup_platform(hass, [Platform.CLIMATE])

    assert_entities(hass, entry.entry_id, entity_registry, snapshot)

    entity_id = "climate.test_climate"

    # Turn On and Set Temp
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: [entity_id],
            ATTR_TEMPERATURE: 20,
            ATTR_HVAC_MODE: HVACMode.HEAT_COOL,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 20
    assert state.state == HVACMode.HEAT_COOL

    # Set Temp
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: [entity_id],
            ATTR_TEMPERATURE: 21,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 21

    # Set Preset
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_PRESET_MODE: "keep"},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PRESET_MODE] == "keep"

    # Set Preset
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_PRESET_MODE: "off"},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PRESET_MODE] == "off"

    # Turn Off
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF

    entity_id = "climate.test_cabin_overheat_protection"

    # Turn On and Set Low
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: [entity_id],
            ATTR_TEMPERATURE: 30,
            ATTR_HVAC_MODE: HVACMode.FAN_ONLY,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 30
    assert state.state == HVACMode.FAN_ONLY

    # Set Temp Medium
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: [entity_id],
            ATTR_TEMPERATURE: 35,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 35

    # Set Temp High
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: [entity_id],
            ATTR_TEMPERATURE: 40,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 40

    # Turn Off
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF

    # Turn On
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.COOL

    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 40
    assert state.state == HVACMode.COOL

    # pytest raises ServiceValidationError
    with pytest.raises(
        ServiceValidationError,
        match="Cabin overheat protection does not support that temperature",
    ):
        # Invalid Temp
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: [entity_id], ATTR_TEMPERATURE: 34},
            blocking=True,
        )