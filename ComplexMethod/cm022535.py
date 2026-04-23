async def test_snapshot_service(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the snapshot option."""
    assert await async_setup_component(hass, "scene", {"scene": {}})
    await hass.async_block_till_done()
    hass.states.async_set("light.my_light", "on", {"hs_color": (345, 75)})
    assert hass.states.get("scene.hallo") is None

    await hass.services.async_call(
        "scene",
        "create",
        {"scene_id": "hallo", "snapshot_entities": ["light.my_light"]},
        blocking=True,
    )
    await hass.async_block_till_done()
    scene = hass.states.get("scene.hallo")
    assert scene is not None
    assert scene.attributes.get("entity_id") == ["light.my_light"]

    hass.states.async_set("light.my_light", "off", {"hs_color": (123, 45)})
    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    await hass.services.async_call(
        "scene", "turn_on", {"entity_id": "scene.hallo"}, blocking=True
    )
    await hass.async_block_till_done()
    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].data.get("entity_id") == "light.my_light"
    assert turn_on_calls[0].data.get("hs_color") == (345, 75)

    await hass.services.async_call(
        "scene",
        "create",
        {"scene_id": "hallo_2", "snapshot_entities": ["light.not_existent"]},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("scene.hallo_2") is None
    assert (
        "Entity light.not_existent does not exist and therefore cannot be snapshotted"
        in caplog.text
    )

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo_3",
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
            "snapshot_entities": ["light.my_light"],
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    scene = hass.states.get("scene.hallo_3")
    assert scene is not None
    assert "light.my_light" in scene.attributes.get("entity_id")
    assert "light.bed_light" in scene.attributes.get("entity_id")