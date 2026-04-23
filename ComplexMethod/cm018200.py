async def test_subscribe_unsubscribe_entities(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
) -> None:
    """Test subscribe/unsubscribe entities."""

    hass.states.async_set("light.permitted", "off", {"color": "red"})
    original_state = hass.states.get("light.permitted")
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
    hass_admin_user.mock_policy({"entities": {"entity_ids": {"light.permitted": True}}})
    assert not hass_admin_user.is_admin

    await websocket_client.send_json_auto_id({"type": "subscribe_entities"})

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert isinstance(msg["event"]["a"]["light.permitted"]["c"], str)
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
    hass.states.async_set("light.not_permitted", "on")
    hass.states.async_set("light.permitted", "on", {"color": "blue"})
    hass.states.async_set("light.permitted", "on", {"effect": "help"})
    hass.states.async_set(
        "light.permitted", "on", {"effect": "help", "color": ["blue", "green"]}
    )
    hass.states.async_remove("light.permitted")
    hass.states.async_set("light.permitted", "on", {"effect": "help", "color": "blue"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {
            "light.permitted": {
                "+": {
                    "a": {"color": "blue"},
                    "c": ANY,
                    "lc": ANY,
                    "s": "on",
                }
            }
        }
    }

    change_set = msg["event"]["c"]["light.permitted"]
    additions = deepcopy(change_set["+"])
    _apply_entities_changes(state_dict, change_set)
    assert state_dict == {
        "attributes": {"color": "blue"},
        "context": {
            "id": additions["c"],
            "parent_id": None,
            "user_id": None,
        },
        "entity_id": "light.permitted",
        "last_changed": additions["lc"],
        "last_updated": additions["lc"],
        "state": "on",
    }

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {
            "light.permitted": {
                "+": {
                    "a": {"effect": "help"},
                    "c": ANY,
                    "lu": ANY,
                },
                "-": {"a": ["color"]},
            }
        }
    }

    change_set = msg["event"]["c"]["light.permitted"]
    additions = deepcopy(change_set["+"])
    _apply_entities_changes(state_dict, change_set)

    assert state_dict == {
        "attributes": {"effect": "help"},
        "context": {
            "id": additions["c"],
            "parent_id": None,
            "user_id": None,
        },
        "entity_id": "light.permitted",
        "last_changed": ANY,
        "last_updated": additions["lu"],
        "state": "on",
    }

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {
            "light.permitted": {
                "+": {
                    "a": {"color": ["blue", "green"]},
                    "c": ANY,
                    "lu": ANY,
                }
            }
        }
    }

    change_set = msg["event"]["c"]["light.permitted"]
    additions = deepcopy(change_set["+"])
    _apply_entities_changes(state_dict, change_set)

    assert state_dict == {
        "attributes": {"effect": "help", "color": ["blue", "green"]},
        "context": {
            "id": additions["c"],
            "parent_id": None,
            "user_id": None,
        },
        "entity_id": "light.permitted",
        "last_changed": ANY,
        "last_updated": additions["lu"],
        "state": "on",
    }

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {"r": ["light.permitted"]}

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "a": {
            "light.permitted": {
                "a": {"color": "blue", "effect": "help"},
                "c": ANY,
                "lc": ANY,
                "s": "on",
            }
        }
    }