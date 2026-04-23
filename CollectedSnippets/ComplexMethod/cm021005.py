async def test_load(
    hass: HomeAssistant,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
) -> None:
    """Test set up from storage and YAML."""
    assert await schedule_setup()

    state = hass.states.get(f"{DOMAIN}.from_storage")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_FRIENDLY_NAME] == "from storage"
    assert state.attributes[ATTR_EDITABLE] is True
    assert state.attributes[ATTR_ICON] == "mdi:party-popper"
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-08-12T17:00:00-07:00"

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_FRIENDLY_NAME] == "from yaml"
    assert state.attributes[ATTR_EDITABLE] is False
    assert state.attributes[ATTR_ICON] == "mdi:party-pooper"
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-08-10T23:59:59-07:00"