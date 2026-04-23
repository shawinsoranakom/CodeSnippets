async def test_measures_scheduling(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_ondilo_client: MagicMock,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
) -> None:
    """Test refresh scheduling of measures coordinator."""
    # Move time to 10 min after pool 1 was updated and 5 min after pool 2 was updated.
    freezer.move_to("2024-01-01T01:10:00+00:00")
    entity_id_1 = "sensor.pool_1_temperature"
    entity_id_2 = "sensor.pool_2_temperature"
    await setup_integration(hass, config_entry, mock_ondilo_client)

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )

    # Two pools are created with 7 entities each.
    assert len(device_entries) == 2
    assert len(hass.states.async_all()) == 14

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T01:10:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T01:10:00+00:00")

    # Tick time by 20 min.
    # The measures coordinators for both pools should not have been refreshed again.
    freezer.tick(timedelta(minutes=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T01:10:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T01:10:00+00:00")

    # Move time to 65 min after pool 1 was last updated.
    # This is 5 min after we expect pool 1 to be updated again.
    # The measures coordinator for pool 1 should refresh at this time.
    # The measures coordinator for pool 2 should not have been refreshed again.
    # The pools coordinator has updated the last update time
    # of the pools to a stale time that is already passed.
    freezer.move_to("2024-01-01T02:05:00+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T02:05:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T01:10:00+00:00")

    # Tick time by 5 min.
    # The measures coordinator for pool 1 should not have been refreshed again.
    # The measures coordinator for pool 2 should refresh at this time.
    # The pools coordinator has updated the last update time
    # of the pools to a stale time that is already passed.
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T02:05:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T02:10:00+00:00")

    # Tick time by 55 min.
    # The measures coordinator for pool 1 should refresh at this time.
    # This is 1 hour after the last refresh of the measures coordinator for pool 1.
    freezer.tick(timedelta(minutes=55))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T03:05:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T02:10:00+00:00")

    # Tick time by 5 min.
    # The measures coordinator for pool 2 should refresh at this time.
    # This is 1 hour after the last refresh of the measures coordinator for pool 2.
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T03:05:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T03:10:00+00:00")

    # Set an error on the pools coordinator endpoint.
    # This will cause the pools coordinator to not update the next refresh.
    # This should cause the measures coordinators to keep the 1 hour cadence.
    mock_ondilo_client.get_pools.side_effect = OndiloError(
        502,
        (
            "<html> <head><title>502 Bad Gateway</title></head> "
            "<body> <center><h1>502 Bad Gateway</h1></center> </body> </html>"
        ),
    )

    # Tick time by 55 min.
    # The measures coordinator for pool 1 should refresh at this time.
    # This is 1 hour after the last refresh of the measures coordinator for pool 1.
    freezer.tick(timedelta(minutes=55))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T04:05:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T03:10:00+00:00")

    # Tick time by 5 min.
    # The measures coordinator for pool 2 should refresh at this time.
    # This is 1 hour after the last refresh of the measures coordinator for pool 2.
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id_1)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T04:05:00+00:00")
    state = hass.states.get(entity_id_2)
    assert state is not None
    assert state.last_reported == datetime.fromisoformat("2024-01-01T04:10:00+00:00")