async def test_task_items_error_response(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test an error while the entity updates getting a new list of todo list items."""

    assert await integration_setup()

    # Test successful setup and first data fetch
    state = hass.states.get("todo.my_tasks")
    assert state
    assert state.state == "1"

    # Next update fails
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("todo.my_tasks")
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Next update succeeds
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("todo.my_tasks")
    assert state
    assert state.state == "1"