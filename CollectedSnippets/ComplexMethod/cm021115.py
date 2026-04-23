async def test_select_ptz_patrol_websocket_update(
    hass: HomeAssistant, ufp: MockUFPFixture, ptz_camera: Camera
) -> None:
    """Test PTZ patrol state updates via websocket."""
    patrols = _make_patrols(ptz_camera.id)
    await _setup_ptz_camera(hass, ufp, ptz_camera, patrols=patrols)

    entity_id = _get_ptz_entity_id(hass, ptz_camera, "ptz_patrol")
    assert entity_id is not None

    # Initially stopped
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == PTZ_PATROL_STOP

    # Simulate websocket update: patrol starts
    new_camera = ptz_camera.model_copy()
    new_camera.active_patrol_slot = 1

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_camera

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "Patrol 2"

    # Simulate websocket update: patrol stops
    new_camera2 = ptz_camera.model_copy()
    new_camera2.active_patrol_slot = None

    mock_msg2 = Mock()
    mock_msg2.changed_data = {}
    mock_msg2.new_obj = new_camera2

    ufp.api.bootstrap.cameras = {new_camera2.id: new_camera2}
    ufp.ws_msg(mock_msg2)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == PTZ_PATROL_STOP