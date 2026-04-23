async def test_turn_on_off_toggle(
    hass: HomeAssistant, toggle: bool, action_schema_variations: str
) -> None:
    """Verify turn_on, turn_off & toggle services.

    Ensures backward compatibility with the old service action schema is maintained.
    """
    event = "test_event"
    event_mock = Mock()

    hass.bus.async_listen(event, event_mock)

    was_on = False

    @callback
    def state_listener(entity_id, old_state, new_state):
        nonlocal was_on
        was_on = True

    async_track_state_change(hass, ENTITY_ID, state_listener, to_state="on")

    if toggle:
        turn_off_step = {
            action_schema_variations: "script.toggle",
            "entity_id": ENTITY_ID,
        }
    else:
        turn_off_step = {
            action_schema_variations: "script.turn_off",
            "entity_id": ENTITY_ID,
        }
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test": {
                    "sequence": [{"event": event}, turn_off_step, {"event": event}]
                }
            }
        },
    )

    assert not script.is_on(hass, ENTITY_ID)

    if toggle:
        await hass.services.async_call(
            DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_ID}
        )
    else:
        await hass.services.async_call(DOMAIN, split_entity_id(ENTITY_ID)[1])
    await hass.async_block_till_done()

    assert not script.is_on(hass, ENTITY_ID)
    assert was_on
    assert event_mock.call_count == 1