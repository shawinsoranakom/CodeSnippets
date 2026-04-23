async def test_entity_play_media_cast_invalid(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
    quick_play_mock,
) -> None:
    """Test playing media."""
    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    _, conn_status_cb, _ = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "off"
    assert entity_id == entity_registry.async_get_entity_id(
        "media_player", "cast", str(info.uuid)
    )

    # play_media - media_type cast with invalid JSON
    with pytest.raises(json.decoder.JSONDecodeError):
        await common.async_play_media(hass, "cast", '{"app_id": "abc123"', entity_id)
    assert "Invalid JSON in media_content_id" in caplog.text
    chromecast.start_app.assert_not_called()
    quick_play_mock.assert_not_called()

    # Play_media - media_type cast with extra keys
    await common.async_play_media(
        hass, "cast", '{"app_id": "abc123", "extra": "data"}', entity_id
    )
    assert "Extra keys dict_keys(['extra']) were ignored" in caplog.text
    chromecast.start_app.assert_called_once_with("abc123")
    quick_play_mock.assert_not_called()

    # Play_media - media_type cast with unsupported app
    quick_play_mock.side_effect = NotImplementedError()
    await common.async_play_media(hass, "cast", '{"app_name": "unknown"}', entity_id)
    quick_play_mock.assert_called_once_with(ANY, "unknown", {})
    assert "App unknown not supported" in caplog.text