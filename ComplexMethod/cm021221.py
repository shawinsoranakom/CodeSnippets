async def test_cover_positions(
    hass: HomeAssistant,
    mock_homee: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test an open cover."""
    # Cover open, tilt open.
    # mock_homee.nodes = [cover]
    mock_homee.nodes = [build_mock_node("cover_with_position_slats.json")]
    mock_homee.get_node_by_id.return_value = mock_homee.nodes[0]
    cover = mock_homee.nodes[0]

    await setup_integration(hass, mock_config_entry)

    assert hass.states.get("cover.test_cover").state == CoverState.OPEN

    attributes = hass.states.get("cover.test_cover").attributes
    assert attributes.get("supported_features") == (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_TILT_POSITION
    )
    assert attributes.get("current_position") == 100
    assert attributes.get("current_tilt_position") == 100

    cover.attributes[0].current_value = 1
    cover.attributes[1].current_value = 100
    cover.attributes[2].current_value = 90
    cover.add_on_changed_listener.call_args_list[0][0][0](cover)
    await hass.async_block_till_done()

    attributes = hass.states.get("cover.test_cover").attributes
    assert attributes.get("current_position") == 0
    assert attributes.get("current_tilt_position") == 0
    assert hass.states.get("cover.test_cover").state == CoverState.CLOSED

    cover.attributes[0].current_value = 3
    cover.attributes[1].current_value = 75
    cover.attributes[2].current_value = 56
    cover.add_on_changed_listener.call_args_list[0][0][0](cover)
    await hass.async_block_till_done()

    assert hass.states.get("cover.test_cover").state == CoverState.OPENING
    attributes = hass.states.get("cover.test_cover").attributes
    assert attributes.get("current_position") == 25
    assert attributes.get("current_tilt_position") == 25

    cover.attributes[0].current_value = 4
    cover.attributes[1].current_value = 25
    cover.attributes[2].current_value = -11
    cover.add_on_changed_listener.call_args_list[0][0][0](cover)
    await hass.async_block_till_done()

    assert hass.states.get("cover.test_cover").state == CoverState.CLOSING
    attributes = hass.states.get("cover.test_cover").attributes
    assert attributes.get("current_position") == 75
    assert attributes.get("current_tilt_position") == 74