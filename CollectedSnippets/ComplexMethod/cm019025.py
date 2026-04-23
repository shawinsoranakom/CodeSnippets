async def test_handler_google_actions(hass: HomeAssistant) -> None:
    """Test handler Google Actions."""
    hass.states.async_set("switch.test", "on", {"friendly_name": "Test switch"})
    hass.states.async_set("switch.test2", "on", {"friendly_name": "Test switch 2"})
    hass.states.async_set("group.all_locks", "on", {"friendly_name": "Evil locks"})

    await mock_cloud(
        hass,
        {
            "google_actions": {
                "filter": {"exclude_entities": "switch.test2"},
                "entity_config": {
                    "switch.test": {
                        "name": "Config name",
                        "aliases": "Config alias",
                        "room": "living room",
                    }
                },
            }
        },
    )

    mock_cloud_prefs(hass, {})
    cloud = hass.data[DATA_CLOUD]

    reqid = "5711642932632160983"
    data = {"requestId": reqid, "inputs": [{"intent": "action.devices.SYNC"}]}

    with patch(
        "hass_nabucasa.Cloud._decode_claims",
        return_value={"cognito:username": "myUserName"},
    ):
        await cloud.client.get_google_config()
        resp = await cloud.client.async_google_message(data)

    assert resp["requestId"] == reqid
    payload = resp["payload"]

    assert payload["agentUserId"] == "myUserName"

    devices = payload["devices"]
    assert len(devices) == 1

    device = devices[0]
    assert device["id"] == "switch.test"
    assert device["name"]["name"] == "Config name"
    assert device["name"]["nicknames"] == ["Config name", "Config alias"]
    assert device["type"] == "action.devices.types.SWITCH"
    assert device["roomHint"] == "living room"