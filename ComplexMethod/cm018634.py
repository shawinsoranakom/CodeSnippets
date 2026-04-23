async def test_fallback_to_polling(
    hass: HomeAssistant,
    config_entry,
    soco,
    fire_zgs_event,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that polling fallback works."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    # Do not wait on background tasks here because the
    # subscription callback will fire an unsub the polling check
    await hass.async_block_till_done()
    await fire_zgs_event()

    speaker = list(config_entry.runtime_data.discovered.values())[0]
    assert speaker.soco is soco
    assert speaker._subscriptions
    assert not speaker.subscriptions_failed

    caplog.clear()

    # Ensure subscriptions are cancelled and polling methods are called when subscriptions time out
    with (
        patch("homeassistant.components.sonos.media.SonosMedia.poll_media"),
        patch(
            "homeassistant.components.sonos.speaker.SonosSpeaker.subscription_address"
        ),
    ):
        async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert not speaker._subscriptions
    assert speaker.subscriptions_failed
    assert "Activity on Zone A from SonosSpeaker.update_volume" in caplog.text