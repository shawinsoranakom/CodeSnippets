async def test_entity_media_states_active_input(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test various entity media states when the lovelace app is active."""
    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    chromecast.cast_type = pychromecast.const.CAST_TYPE_CHROMECAST
    cast_status_cb, conn_status_cb, _ = get_status_callbacks(chromecast)

    chromecast.app_id = "84912283"
    cast_status = MagicMock()

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await hass.async_block_till_done()

    # Unknown input status
    cast_status.is_active_input = None
    cast_status_cb(cast_status)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "idle"

    # Active input status
    cast_status.is_active_input = True
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "idle"

    # Inactive input status
    cast_status.is_active_input = False
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"

    # Inactive input status, but ignored
    chromecast.ignore_cec = True
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "idle"