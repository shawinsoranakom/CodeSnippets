async def test_group_media_states_early(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mz_mock
) -> None:
    """Test media states are read from group if entity has no state.

    This tests case asserts group state is polled when the player is created.
    """
    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info()

    mz_mock.get_multizone_memberships = MagicMock(return_value=[str(FakeGroupUUID)])
    mz_mock.get_multizone_mediacontroller = MagicMock(
        return_value=MagicMock(status=MagicMock(images=None, player_state="BUFFERING"))
    )

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    _, conn_status_cb, _, _ = get_status_callbacks(chromecast, mz_mock)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unavailable"
    assert entity_id == entity_registry.async_get_entity_id(
        "media_player", "cast", str(info.uuid)
    )

    # Check group state is polled when player is first created
    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "buffering"

    connection_status = MagicMock()
    connection_status.status = "LOST"
    conn_status_cb(connection_status)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "unavailable"

    # Check group state is polled when player reconnects
    mz_mock.get_multizone_mediacontroller = MagicMock(
        return_value=MagicMock(status=MagicMock(images=None, player_state="PLAYING"))
    )

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "playing"