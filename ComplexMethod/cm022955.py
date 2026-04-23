async def test_switch_services(
    hass: HomeAssistant, dummy_device_from_host_switch
) -> None:
    """Test the services of the switch."""
    await setup_integration(hass)

    # Set watering time
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_WATERING_TIME,
        {ATTR_WATERING_TIME: 30, ATTR_ENTITY_ID: "switch.wl000000000099_1_watering"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.attributes.get(ATTR_WATERING_TIME) == 30

    # Set pause time
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_PAUSE_TIME,
        {ATTR_PAUSE_TIME: 18, ATTR_ENTITY_ID: "switch.wl000000000099_2_pause"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_2_pause")
    assert state
    assert state.attributes.get(ATTR_PAUSE_TIME) == 18

    # Set trigger_1
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_TRIGGER,
        {
            ATTR_TRIGGER_INDEX: "1",
            ATTR_TRIGGER: "12715301",
            ATTR_ENTITY_ID: "switch.wl000000000099_1_watering",
        },
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.attributes.get(ATTR_TRIGGER_1) == "12715301"

    # Set trigger_2
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_TRIGGER,
        {
            ATTR_TRIGGER_INDEX: "2",
            ATTR_TRIGGER: "12707301",
            ATTR_ENTITY_ID: "switch.wl000000000099_1_watering",
        },
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.attributes.get(ATTR_TRIGGER_2) == "12707301"

    # Set trigger_3
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_TRIGGER,
        {
            ATTR_TRIGGER_INDEX: "3",
            ATTR_TRIGGER: "00015301",
            ATTR_ENTITY_ID: "switch.wl000000000099_1_watering",
        },
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.attributes.get(ATTR_TRIGGER_3) == "00015301"

    # Set trigger_4
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_TRIGGER,
        {
            ATTR_TRIGGER_INDEX: "4",
            ATTR_TRIGGER: "00008300",
            ATTR_ENTITY_ID: "switch.wl000000000099_1_watering",
        },
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.attributes.get(ATTR_TRIGGER_4) == "00008300"

    # Set watering time using WiLight Pause Switch to raise
    with pytest.raises(TypeError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_WATERING_TIME,
            {ATTR_WATERING_TIME: 30, ATTR_ENTITY_ID: "switch.wl000000000099_2_pause"},
            blocking=True,
        )

    assert str(exc_info.value) == "Entity is not a WiLight valve switch"