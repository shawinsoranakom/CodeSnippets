async def test_allow_clip_sensor(
    hass: HomeAssistant, config_entry_setup: MockConfigEntry
) -> None:
    """Test that CLIP sensors can be allowed."""

    assert len(hass.states.async_all()) == 3
    assert hass.states.get("binary_sensor.presence_sensor").state == STATE_OFF
    assert hass.states.get("binary_sensor.clip_presence_sensor").state == STATE_OFF
    assert hass.states.get("binary_sensor.clip_flag_boot_time").state == STATE_ON

    # Disallow clip sensors

    hass.config_entries.async_update_entry(
        config_entry_setup, options={CONF_ALLOW_CLIP_SENSOR: False}
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1
    assert not hass.states.get("binary_sensor.clip_presence_sensor")
    assert not hass.states.get("binary_sensor.clip_flag_boot_time")

    # Allow clip sensors

    hass.config_entries.async_update_entry(
        config_entry_setup, options={CONF_ALLOW_CLIP_SENSOR: True}
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 3
    assert hass.states.get("binary_sensor.clip_presence_sensor").state == STATE_OFF
    assert hass.states.get("binary_sensor.clip_flag_boot_time").state == STATE_ON