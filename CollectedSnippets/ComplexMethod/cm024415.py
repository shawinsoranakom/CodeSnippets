async def test_ignore_transient_devices_unless_we_see_them_a_few_times(
    hass: HomeAssistant,
) -> None:
    """Test we ignore transient devices unless we see them a few times."""
    entry = MockConfigEntry(
        domain=DOMAIN,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    before_entity_count = len(hass.states.async_entity_ids())
    inject_bluetooth_service_info(
        hass,
        TESLA_TRANSIENT,
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids()) == before_entity_count

    with patch_all_discovered_devices([TESLA_TRANSIENT_BLE_DEVICE]):
        async_fire_time_changed(
            hass,
            dt_util.utcnow() + timedelta(seconds=UPDATE_INTERVAL.total_seconds() * 2),
        )
        await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids()) == before_entity_count

    for i in range(3, 17):
        with patch_all_discovered_devices([TESLA_TRANSIENT_BLE_DEVICE]):
            async_fire_time_changed(
                hass,
                dt_util.utcnow()
                + timedelta(seconds=UPDATE_INTERVAL.total_seconds() * 2 * i),
            )
            await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids()) > before_entity_count

    assert hass.states.get("device_tracker.s6da7c9389bd5452cc_cccc").state == STATE_HOME

    await hass.config_entries.async_reload(entry.entry_id)

    await hass.async_block_till_done()
    assert hass.states.get("device_tracker.s6da7c9389bd5452cc_cccc").state == STATE_HOME