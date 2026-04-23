async def test_state_diff_event(hass: HomeAssistant) -> None:
    """Test building state_diff_message."""
    state_change_events = async_capture_events(hass, EVENT_STATE_CHANGED)
    context = Context(user_id="user-id", parent_id="parent-id", id="id")
    hass.states.async_set("light.window", "on", context=context)
    hass.states.async_set("light.window", "off", context=context)
    await hass.async_block_till_done()

    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)
    assert message == {
        "c": {
            "light.window": {"+": {"lc": new_state.last_changed_timestamp, "s": "off"}}
        }
    }

    hass.states.async_set(
        "light.window",
        "red",
        context=Context(user_id="user-id", parent_id="new-parent-id", id="id"),
    )
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)

    assert message == {
        "c": {
            "light.window": {
                "+": {
                    "c": {"parent_id": "new-parent-id"},
                    "lc": new_state.last_changed_timestamp,
                    "s": "red",
                }
            }
        }
    }

    hass.states.async_set(
        "light.window",
        "green",
        context=Context(
            user_id="new-user-id", parent_id="another-new-parent-id", id="id"
        ),
    )
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)

    assert message == {
        "c": {
            "light.window": {
                "+": {
                    "c": {
                        "parent_id": "another-new-parent-id",
                        "user_id": "new-user-id",
                    },
                    "lc": new_state.last_changed_timestamp,
                    "s": "green",
                }
            }
        }
    }

    hass.states.async_set(
        "light.window",
        "blue",
        context=Context(
            user_id="another-new-user-id", parent_id="another-new-parent-id", id="id"
        ),
    )
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)

    assert message == {
        "c": {
            "light.window": {
                "+": {
                    "c": {"user_id": "another-new-user-id"},
                    "lc": new_state.last_changed_timestamp,
                    "s": "blue",
                }
            }
        }
    }

    hass.states.async_set(
        "light.window",
        "yellow",
        context=Context(
            user_id="another-new-user-id",
            parent_id="another-new-parent-id",
            id="id-new",
        ),
    )
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)

    assert message == {
        "c": {
            "light.window": {
                "+": {
                    "c": "id-new",
                    "lc": new_state.last_changed_timestamp,
                    "s": "yellow",
                }
            }
        }
    }

    new_context = Context()
    hass.states.async_set(
        "light.window", "purple", {"new": "attr"}, context=new_context
    )
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)

    assert message == {
        "c": {
            "light.window": {
                "+": {
                    "a": {"new": "attr"},
                    "c": {"id": new_context.id, "parent_id": None, "user_id": None},
                    "lc": new_state.last_changed_timestamp,
                    "s": "purple",
                }
            }
        }
    }

    hass.states.async_set("light.window", "green", {}, context=new_context)
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)

    assert message == {
        "c": {
            "light.window": {
                "+": {"lc": new_state.last_changed_timestamp, "s": "green"},
                "-": {"a": ["new"]},
            }
        }
    }

    hass.states.async_set(
        "light.window",
        "green",
        {"list_attr": ["a", "b", "c", "d"], "list_attr_2": ["a", "b"]},
        context=new_context,
    )
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)

    assert message == {
        "c": {
            "light.window": {
                "+": {
                    "a": {"list_attr": ["a", "b", "c", "d"], "list_attr_2": ["a", "b"]},
                    "lu": new_state.last_updated_timestamp,
                }
            }
        }
    }

    hass.states.async_set(
        "light.window",
        "green",
        {"list_attr": ["a", "b", "c", "e"]},
        context=new_context,
    )
    await hass.async_block_till_done()
    last_state_event: Event = state_change_events[-1]
    new_state: State = last_state_event.data["new_state"]
    message = _state_diff_event(last_state_event)
    assert message == {
        "c": {
            "light.window": {
                "+": {
                    "a": {"list_attr": ["a", "b", "c", "e"]},
                    "lu": new_state.last_updated_timestamp,
                },
                "-": {"a": ["list_attr_2"]},
            }
        }
    }