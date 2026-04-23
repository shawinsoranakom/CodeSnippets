async def test_nested_group(hass: HomeAssistant) -> None:
    """Test nested lock group."""
    await async_setup_component(
        hass,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": ["lock.some_group"],
                    "name": "Nested Group",
                },
                {
                    "platform": DOMAIN,
                    "entities": [
                        "lock.front_door",
                        "lock.kitchen_door",
                    ],
                    "name": "Some Group",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("lock.some_group")
    assert state is not None
    assert state.state == LockState.UNLOCKED
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        "lock.front_door",
        "lock.kitchen_door",
    ]

    state = hass.states.get("lock.nested_group")
    assert state is not None
    assert state.state == LockState.UNLOCKED
    assert state.attributes.get(ATTR_ENTITY_ID) == ["lock.some_group"]

    # Test controlling the nested group
    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {ATTR_ENTITY_ID: "lock.nested_group"},
        blocking=True,
    )
    assert hass.states.get("lock.front_door").state == LockState.LOCKED
    assert hass.states.get("lock.kitchen_door").state == LockState.LOCKED
    assert hass.states.get("lock.some_group").state == LockState.LOCKED
    assert hass.states.get("lock.nested_group").state == LockState.LOCKED