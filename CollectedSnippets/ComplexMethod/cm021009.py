async def test_ws_create(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
    freezer: FrozenDateTimeFactory,
    to: str,
    next_event: str,
    saved_to: str,
) -> None:
    """Test create WS."""
    freezer.move_to("2022-08-11 8:52:00-07:00")

    assert await schedule_setup(items=[])

    state = hass.states.get("schedule.party_mode")
    assert state is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "party_mode") is None

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": f"{DOMAIN}/create",
            "name": "Party mode",
            "icon": "mdi:party-popper",
            "monday": [{"from": "12:00:00", "to": to}],
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = hass.states.get("schedule.party_mode")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_FRIENDLY_NAME] == "Party mode"
    assert state.attributes[ATTR_EDITABLE] is True
    assert state.attributes[ATTR_ICON] == "mdi:party-popper"
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-08-15T12:00:00-07:00"

    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)

    state = hass.states.get("schedule.party_mode")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == next_event

    await client.send_json({"id": 2, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 1
    assert result["party_mode"][CONF_MONDAY] == [
        {CONF_FROM: "12:00:00", CONF_TO: saved_to}
    ]