async def test_hygrostat_power_state(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "humidifier.test"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_HUMIDITY: 43},
    )
    await hass.async_block_till_done()
    acc = HumidifierDehumidifier(
        hass, hk_driver, "HumidifierDehumidifier", entity_id, 1, None
    )
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_current_humidifier_dehumidifier.value == 2
    assert acc.char_target_humidifier_dehumidifier.value == 1
    assert acc.char_active.value == 1

    hass.states.async_set(
        entity_id,
        STATE_OFF,
        {ATTR_HUMIDITY: 43},
    )
    await hass.async_block_till_done()
    assert acc.char_current_humidifier_dehumidifier.value == 0
    assert acc.char_target_humidifier_dehumidifier.value == 1
    assert acc.char_active.value == 0

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, HUMIDIFIER_DOMAIN, SERVICE_TURN_ON)

    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_turn_on) == 1
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_active.value == 1
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "Active to 1"

    call_turn_off = async_mock_service(hass, HUMIDIFIER_DOMAIN, SERVICE_TURN_OFF)

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_turn_off) == 1
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_active.value == 0
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "Active to 0"