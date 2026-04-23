async def test_measures_error_one_pool(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_ondilo_client: MagicMock,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
    last_measures: list[dict[str, Any]],
) -> None:
    """Test measures error for one pool and success for the other."""
    entity_id_1 = "sensor.pool_1_temperature"
    entity_id_2 = "sensor.pool_2_temperature"
    mock_ondilo_client.get_last_pool_measures.side_effect = [
        OndiloError(
            404,
            "Not Found",
        ),
        last_measures,
    ]

    await setup_integration(hass, config_entry, mock_ondilo_client)

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )

    assert len(device_entries) == 2
    # One pool returned an error, the other is ok.
    # 7 entities are created for the second pool.
    assert len(hass.states.async_all()) == 7
    assert hass.states.get(entity_id_1) is None
    assert hass.states.get(entity_id_2) is not None

    # All pools now return measures.
    mock_ondilo_client.get_last_pool_measures.side_effect = None

    # Move time to next pools coordinator refresh.
    freezer.tick(timedelta(minutes=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )

    assert len(device_entries) == 2
    # 14 entities in total, 7 entities per pool.
    assert len(hass.states.async_all()) == 14
    assert hass.states.get(entity_id_1) is not None
    assert hass.states.get(entity_id_2) is not None