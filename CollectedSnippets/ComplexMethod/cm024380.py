async def test_update_sources_live_tv_find(hass: HomeAssistant, client) -> None:
    """Test finding live TV app id in update sources."""
    await setup_webostv(hass)
    await client.mock_state_update()

    # Live TV found in app list
    sources = hass.states.get(ENTITY_ID).attributes[ATTR_INPUT_SOURCE_LIST]

    assert "Live TV" in sources
    assert len(sources) == 3

    # Live TV is current app
    client.tv_state.apps = {
        LIVE_TV_APP_ID: {
            "title": "Live TV",
            "id": "some_id",
        },
    }
    client.tv_state.current_app_id = "some_id"
    await client.mock_state_update()
    sources = hass.states.get(ENTITY_ID).attributes[ATTR_INPUT_SOURCE_LIST]

    assert "Live TV" in sources
    assert len(sources) == 3

    # Live TV is is in inputs
    client.tv_state.inputs = {
        LIVE_TV_APP_ID: {
            "label": "Live TV",
            "id": "some_id",
            "appId": LIVE_TV_APP_ID,
        },
    }
    await client.mock_state_update()
    sources = hass.states.get(ENTITY_ID).attributes[ATTR_INPUT_SOURCE_LIST]

    assert "Live TV" in sources
    assert len(sources) == 1

    # Live TV is current input
    client.tv_state.inputs = {
        LIVE_TV_APP_ID: {
            "label": "Live TV",
            "id": "some_id",
            "appId": "some_id",
        },
    }
    await client.mock_state_update()
    sources = hass.states.get(ENTITY_ID).attributes[ATTR_INPUT_SOURCE_LIST]

    assert "Live TV" in sources
    assert len(sources) == 1

    # Live TV not found
    client.tv_state.current_app_id = "other_id"
    await client.mock_state_update()
    sources = hass.states.get(ENTITY_ID).attributes[ATTR_INPUT_SOURCE_LIST]

    assert "Live TV" in sources
    assert len(sources) == 1

    # Live TV not found in sources/apps but is current app
    client.tv_state.apps = {}
    client.tv_state.current_app_id = LIVE_TV_APP_ID
    await client.mock_state_update()
    sources = hass.states.get(ENTITY_ID).attributes[ATTR_INPUT_SOURCE_LIST]

    assert "Live TV" in sources
    assert len(sources) == 1

    # Bad update, keep old update
    client.tv_state.inputs = {}
    await client.mock_state_update()
    sources = hass.states.get(ENTITY_ID).attributes[ATTR_INPUT_SOURCE_LIST]

    assert "Live TV" in sources
    assert len(sources) == 1