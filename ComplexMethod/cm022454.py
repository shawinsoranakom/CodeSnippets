async def test_scene_script(hass: HomeAssistant) -> None:
    """Test Scene trait support for script domain."""
    assert helpers.get_google_type(script.DOMAIN, None) is not None
    assert trait.SceneTrait.supported(script.DOMAIN, 0, None, None)

    trt = trait.SceneTrait(hass, State("script.bla", STATE_OFF), BASIC_CONFIG)
    assert trt.sync_attributes() == {}
    assert trt.query_attributes() == {}
    assert trt.can_execute(trait.COMMAND_ACTIVATE_SCENE, {})

    calls = async_mock_service(hass, script.DOMAIN, SERVICE_TURN_ON)
    await trt.execute(trait.COMMAND_ACTIVATE_SCENE, BASIC_DATA, {}, {})

    # We don't wait till script execution is done.
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "script.bla"}