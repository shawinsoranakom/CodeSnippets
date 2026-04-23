async def test_holidy_summer_mode(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, fritz: Mock
) -> None:
    """Test holiday and summer mode."""
    device = FritzDeviceClimateMock()
    device.lock = False

    await setup_config_entry(
        hass, MOCK_CONFIG[DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    # initial state
    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.attributes[ATTR_HVAC_MODES] == [HVACMode.HEAT, HVACMode.OFF]
    assert state.attributes[ATTR_PRESET_MODE] is None
    assert state.attributes[ATTR_PRESET_MODES] == [
        PRESET_ECO,
        PRESET_COMFORT,
        PRESET_BOOST,
    ]

    # test holiday mode
    device.holiday_active = True
    device.summer_active = False
    freezer.tick(timedelta(seconds=200))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.attributes[ATTR_HVAC_MODES] == [HVACMode.HEAT, HVACMode.OFF]
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_HOLIDAY
    assert state.attributes[ATTR_PRESET_MODES] == [PRESET_HOLIDAY]

    with pytest.raises(
        HomeAssistantError,
        match="Can't change settings while holiday or summer mode is active on the device",
    ):
        await hass.services.async_call(
            "climate",
            SERVICE_SET_HVAC_MODE,
            {"entity_id": ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
    with pytest.raises(
        HomeAssistantError,
        match="Can't change settings while holiday or summer mode is active on the device",
    ):
        await hass.services.async_call(
            "climate",
            SERVICE_SET_PRESET_MODE,
            {"entity_id": ENTITY_ID, ATTR_PRESET_MODE: PRESET_HOLIDAY},
            blocking=True,
        )

    # test summer mode
    device.holiday_active = False
    device.summer_active = True
    freezer.tick(timedelta(seconds=200))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.attributes[ATTR_HVAC_MODES] == [HVACMode.HEAT, HVACMode.OFF]
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_SUMMER
    assert state.attributes[ATTR_PRESET_MODES] == [PRESET_SUMMER]

    with pytest.raises(
        HomeAssistantError,
        match="Can't change settings while holiday or summer mode is active on the device",
    ):
        await hass.services.async_call(
            "climate",
            SERVICE_SET_HVAC_MODE,
            {"entity_id": ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
    with pytest.raises(
        HomeAssistantError,
        match="Can't change settings while holiday or summer mode is active on the device",
    ):
        await hass.services.async_call(
            "climate",
            SERVICE_SET_PRESET_MODE,
            {"entity_id": ENTITY_ID, ATTR_PRESET_MODE: PRESET_SUMMER},
            blocking=True,
        )

    # back to normal state
    device.holiday_active = False
    device.summer_active = False
    freezer.tick(timedelta(seconds=200))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.attributes[ATTR_HVAC_MODES] == [HVACMode.HEAT, HVACMode.OFF]
    assert state.attributes[ATTR_PRESET_MODE] is None
    assert state.attributes[ATTR_PRESET_MODES] == [
        PRESET_ECO,
        PRESET_COMFORT,
        PRESET_BOOST,
    ]