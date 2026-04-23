async def test_lawn_mower_set_state(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if Lawn mower accessory and HA are updated accordingly."""
    entity_id = "lawn_mower.mower"

    hass.states.async_set(
        entity_id,
        None,
        {
            ATTR_SUPPORTED_FEATURES: LawnMowerEntityFeature.DOCK
            | LawnMowerEntityFeature.START_MOWING
        },
    )
    await hass.async_block_till_done()

    acc = LawnMower(hass, hk_driver, "LawnMower", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()
    assert acc.aid == 2
    assert acc.category == 8  # Switch

    assert acc.char_on.value == 0

    hass.states.async_set(
        entity_id,
        LawnMowerActivity.MOWING,
        {
            ATTR_SUPPORTED_FEATURES: LawnMowerEntityFeature.DOCK
            | LawnMowerEntityFeature.START_MOWING
        },
    )
    await hass.async_block_till_done()
    assert acc.char_on.value == 1

    hass.states.async_set(
        entity_id,
        LawnMowerActivity.DOCKED,
        {
            ATTR_SUPPORTED_FEATURES: LawnMowerEntityFeature.DOCK
            | LawnMowerEntityFeature.START_MOWING
        },
    )
    await hass.async_block_till_done()
    assert acc.char_on.value == 0

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, LAWN_MOWER_DOMAIN, SERVICE_START_MOWING)
    call_turn_off = async_mock_service(hass, LAWN_MOWER_DOMAIN, SERVICE_DOCK)

    acc.char_on.client_update_value(1)
    await hass.async_block_till_done()
    assert acc.char_on.value == 1
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_on.client_update_value(0)
    await hass.async_block_till_done()
    assert acc.char_on.value == 0
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None