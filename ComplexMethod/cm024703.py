async def test_switch_read_lock_state(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit lock accessory."""
    helper = await setup_test_component(hass, get_next_aid(), create_lock_service)

    state = await helper.async_update(
        ServicesTypes.LOCK_MECHANISM,
        {
            CharacteristicsTypes.LOCK_MECHANISM_CURRENT_STATE: 0,
            CharacteristicsTypes.LOCK_MECHANISM_TARGET_STATE: 0,
        },
    )
    assert state.state == "unlocked"
    assert state.attributes["battery_level"] == 50

    state = await helper.async_update(
        ServicesTypes.LOCK_MECHANISM,
        {
            CharacteristicsTypes.LOCK_MECHANISM_CURRENT_STATE: 1,
            CharacteristicsTypes.LOCK_MECHANISM_TARGET_STATE: 1,
        },
    )
    assert state.state == "locked"

    await helper.async_update(
        ServicesTypes.LOCK_MECHANISM,
        {
            CharacteristicsTypes.LOCK_MECHANISM_CURRENT_STATE: 2,
            CharacteristicsTypes.LOCK_MECHANISM_TARGET_STATE: 1,
        },
    )
    state = await helper.poll_and_get_state()
    assert state.state == "jammed"

    await helper.async_update(
        ServicesTypes.LOCK_MECHANISM,
        {
            CharacteristicsTypes.LOCK_MECHANISM_CURRENT_STATE: 3,
            CharacteristicsTypes.LOCK_MECHANISM_TARGET_STATE: 1,
        },
    )
    state = await helper.poll_and_get_state()
    assert state.state == "unknown"

    await helper.async_update(
        ServicesTypes.LOCK_MECHANISM,
        {
            CharacteristicsTypes.LOCK_MECHANISM_CURRENT_STATE: 0,
            CharacteristicsTypes.LOCK_MECHANISM_TARGET_STATE: 1,
        },
    )
    state = await helper.poll_and_get_state()
    assert state.state == "locking"

    await helper.async_update(
        ServicesTypes.LOCK_MECHANISM,
        {
            CharacteristicsTypes.LOCK_MECHANISM_CURRENT_STATE: 1,
            CharacteristicsTypes.LOCK_MECHANISM_TARGET_STATE: 0,
        },
    )
    state = await helper.poll_and_get_state()
    assert state.state == "unlocking"