async def test_update(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
    to: str,
    next_event: str,
    saved_to: str,
    icon_dict: dict,
) -> None:
    """Test updating the schedule."""
    assert await schedule_setup()

    state = hass.states.get("schedule.from_storage")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_FRIENDLY_NAME] == "from storage"
    assert state.attributes[ATTR_ICON] == "mdi:party-popper"
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-08-12T17:00:00-07:00"
    assert (
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "from_storage") is not None
    )

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": "from_storage",
            CONF_NAME: "Party pooper",
            **icon_dict,
            CONF_MONDAY: [],
            CONF_TUESDAY: [],
            CONF_WEDNESDAY: [{CONF_FROM: "17:00:00", CONF_TO: to}],
            CONF_THURSDAY: [],
            CONF_FRIDAY: [],
            CONF_SATURDAY: [],
            CONF_SUNDAY: [],
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = hass.states.get("schedule.from_storage")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_FRIENDLY_NAME] == "Party pooper"
    assert state.attributes.get(ATTR_ICON) == icon_dict.get(CONF_ICON)
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == next_event

    await client.send_json({"id": 2, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 1
    assert result["from_storage"][CONF_WEDNESDAY] == [
        {CONF_FROM: "17:00:00", CONF_TO: saved_to}
    ]