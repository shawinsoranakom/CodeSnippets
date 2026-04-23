async def test_subscribe_entities_with_unserializable_state(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
) -> None:
    """Test subscribe entities with an unserializeable state."""

    class CannotSerializeMe:
        """Cannot serialize this."""

        def __init__(self) -> None:
            """Init cannot serialize this."""

    hass.states.async_set("light.permitted", "off", {"color": "red"})
    hass.states.async_set(
        "light.cannot_serialize",
        "off",
        {"color": "red", "cannot_serialize": CannotSerializeMe()},
    )
    original_state = hass.states.get("light.cannot_serialize")
    assert isinstance(original_state, State)
    state_dict = {
        "attributes": dict(original_state.attributes),
        "context": dict(original_state.context.as_dict()),
        "entity_id": original_state.entity_id,
        "last_changed": original_state.last_changed.isoformat(),
        "last_updated": original_state.last_updated.isoformat(),
        "state": original_state.state,
    }
    hass_admin_user.groups = []
    hass_admin_user.mock_policy(
        {
            "entities": {
                "entity_ids": {"light.permitted": True, "light.cannot_serialize": True}
            }
        }
    )

    await websocket_client.send_json_auto_id({"type": "subscribe_entities"})

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "a": {
            "light.permitted": {
                "a": {"color": "red"},
                "c": ANY,
                "lc": ANY,
                "s": "off",
            }
        }
    }
    hass.states.async_set("light.permitted", "on", {"effect": "help"})
    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {
            "light.permitted": {
                "+": {
                    "a": {"effect": "help"},
                    "c": ANY,
                    "lc": ANY,
                    "s": "on",
                },
                "-": {"a": ["color"]},
            }
        }
    }
    hass.states.async_set("light.cannot_serialize", "on", {"effect": "help"})
    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    # Order does not matter
    msg["event"]["c"]["light.cannot_serialize"]["-"]["a"] = set(
        msg["event"]["c"]["light.cannot_serialize"]["-"]["a"]
    )
    assert msg["event"] == {
        "c": {
            "light.cannot_serialize": {
                "+": {"a": {"effect": "help"}, "c": ANY, "lc": ANY, "s": "on"},
                "-": {"a": {"color", "cannot_serialize"}},
            }
        }
    }
    change_set = msg["event"]["c"]["light.cannot_serialize"]
    _apply_entities_changes(state_dict, change_set)
    assert state_dict == {
        "attributes": {"effect": "help"},
        "context": {
            "id": ANY,
            "parent_id": None,
            "user_id": None,
        },
        "entity_id": "light.cannot_serialize",
        "last_changed": ANY,
        "last_updated": ANY,
        "state": "on",
    }
    hass.states.async_set(
        "light.cannot_serialize",
        "off",
        {"color": "red", "cannot_serialize": CannotSerializeMe()},
    )
    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "result"
    assert msg["error"] == {
        "code": "unknown_error",
        "message": "Invalid JSON in response",
    }