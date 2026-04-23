async def test_scene_scene(hass: HomeAssistant) -> None:
    """Test Scene trait support for scene domain."""
    assert helpers.get_google_type(scene.DOMAIN, None) is not None
    assert trait.SceneTrait.supported(scene.DOMAIN, 0, None, None)

    trt = trait.SceneTrait(hass, State("scene.bla", STATE_UNKNOWN), BASIC_CONFIG)
    assert trt.sync_attributes() == {}
    assert trt.query_attributes() == {}
    assert trt.can_execute(trait.COMMAND_ACTIVATE_SCENE, {})

    calls = async_mock_service(hass, scene.DOMAIN, SERVICE_TURN_ON)
    await trt.execute(trait.COMMAND_ACTIVATE_SCENE, BASIC_DATA, {}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "scene.bla"}