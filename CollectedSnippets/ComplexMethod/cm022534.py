async def test_create_service(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the create service."""
    assert await async_setup_component(
        hass,
        "scene",
        {"scene": {"name": "hallo_2", "entities": {"light.kitchen": "on"}}},
    )
    await hass.async_block_till_done()
    assert hass.states.get("scene.hallo") is None
    assert hass.states.get("scene.hallo_2") is not None

    await hass.services.async_call(
        "scene",
        "create",
        {"scene_id": "hallo", "entities": {}, "snapshot_entities": []},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert "Empty scenes are not allowed" in caplog.text
    assert hass.states.get("scene.hallo") is None

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo",
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    scene = hass.states.get("scene.hallo")
    assert scene is not None
    assert scene.domain == "scene"
    assert scene.name == "hallo"
    assert scene.state == STATE_UNKNOWN
    assert scene.attributes.get("entity_id") == ["light.bed_light"]

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo",
            "entities": {"light.kitchen_light": {"state": "on", "brightness": 100}},
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    scene = hass.states.get("scene.hallo")
    assert scene is not None
    assert scene.domain == "scene"
    assert scene.name == "hallo"
    assert scene.state == STATE_UNKNOWN
    assert scene.attributes.get("entity_id") == ["light.kitchen_light"]

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo_2",
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    assert "The scene scene.hallo_2 already exists" in caplog.text
    scene = hass.states.get("scene.hallo_2")
    assert scene is not None
    assert scene.domain == "scene"
    assert scene.name == "hallo_2"
    assert scene.state == STATE_UNKNOWN
    assert scene.attributes.get("entity_id") == ["light.kitchen"]