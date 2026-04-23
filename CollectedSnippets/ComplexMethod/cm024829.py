async def test_saving_with_delay_churn_reduction(
    hass: HomeAssistant,
    store: storage.Store,
    hass_storage: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test saving data after a delay with timer churn reduction."""
    store.async_delay_save(lambda: MOCK_DATA, 1)
    assert store.key not in hass_storage

    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key not in hass_storage

    freezer.tick(1)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert hass_storage[store.key] == {
        "version": MOCK_VERSION,
        "minor_version": 1,
        "key": MOCK_KEY,
        "data": MOCK_DATA,
    }

    del hass_storage[store.key]
    # Simulate what some of the registries do when they add 100 entities
    for _ in range(100):
        store.async_delay_save(lambda: MOCK_DATA, 1)

    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key not in hass_storage
    store.async_delay_save(lambda: MOCK_DATA, 1)

    freezer.tick(1)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key in hass_storage

    del hass_storage[store.key]

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(0.5)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key not in hass_storage

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(0.8)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key not in hass_storage

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(0.8)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key not in hass_storage

    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key in hass_storage

    # Make sure if we do another delayed save
    # and one with a shorter delay, the shorter delay wins
    del hass_storage[store.key]
    store.async_delay_save(lambda: MOCK_DATA, 2)
    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key not in hass_storage

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(1.0)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    assert store.key in hass_storage