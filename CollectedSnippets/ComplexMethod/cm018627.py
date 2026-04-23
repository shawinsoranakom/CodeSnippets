async def test_setup_failed(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test failed to set up the entity."""
    mocked_device = _create_mocked_device(throw_exception=True)
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    all_states = hass.states.async_all()
    assert len(all_states) == 0
    assert "[name(http://0.0.0.0:10000/sony)] Unable to connect" in caplog.text
    assert "Platform songpal not ready yet: Unable to do POST request" in caplog.text
    assert not any(x.levelno == logging.ERROR for x in caplog.records)
    caplog.clear()

    utcnow = dt_util.utcnow()
    type(mocked_device).get_supported_methods = AsyncMock()
    with _patch_media_player_device(mocked_device):
        async_fire_time_changed(hass, utcnow + timedelta(seconds=30))
        await hass.async_block_till_done()
    all_states = hass.states.async_all()
    assert len(all_states) == 1
    assert not any(x.levelno == logging.WARNING for x in caplog.records)
    assert not any(x.levelno == logging.ERROR for x in caplog.records)