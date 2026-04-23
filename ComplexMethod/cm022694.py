async def test_vacuum_set_state_with_returnhome_and_start_support(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if Vacuum accessory and HA are updated accordingly."""
    entity_id = "vacuum.roomba"

    hass.states.async_set(
        entity_id,
        None,
        {
            ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.START
        },
    )
    await hass.async_block_till_done()

    acc = Vacuum(hass, hk_driver, "Vacuum", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()
    assert acc.aid == 2
    assert acc.category == 8  # Switch

    assert acc.char_on.value == 0

    hass.states.async_set(
        entity_id,
        VacuumActivity.CLEANING,
        {
            ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.START
        },
    )
    await hass.async_block_till_done()
    assert acc.char_on.value == 1

    hass.states.async_set(
        entity_id,
        VacuumActivity.DOCKED,
        {
            ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.START
        },
    )
    await hass.async_block_till_done()
    assert acc.char_on.value == 0

    # Set from HomeKit
    call_start = async_mock_service(hass, VACUUM_DOMAIN, SERVICE_START)
    call_return_to_base = async_mock_service(
        hass, VACUUM_DOMAIN, SERVICE_RETURN_TO_BASE
    )

    acc.char_on.client_update_value(1)
    await hass.async_block_till_done()
    assert acc.char_on.value == 1
    assert call_start
    assert call_start[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_on.client_update_value(0)
    await hass.async_block_till_done()
    assert acc.char_on.value == 0
    assert call_return_to_base
    assert call_return_to_base[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None