async def test_scene_button(hass: HomeAssistant, component) -> None:
    """Test Scene trait support for the (input) button domain."""
    assert helpers.get_google_type(component.DOMAIN, None) is not None
    assert trait.SceneTrait.supported(component.DOMAIN, 0, None, None)

    trt = trait.SceneTrait(
        hass, State(f"{component.DOMAIN}.bla", STATE_UNKNOWN), BASIC_CONFIG
    )
    assert trt.sync_attributes() == {}
    assert trt.query_attributes() == {}
    assert trt.can_execute(trait.COMMAND_ACTIVATE_SCENE, {})

    calls = async_mock_service(hass, component.DOMAIN, component.SERVICE_PRESS)
    await trt.execute(trait.COMMAND_ACTIVATE_SCENE, BASIC_DATA, {}, {})

    # We don't wait till button press is done.
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: f"{component.DOMAIN}.bla"}