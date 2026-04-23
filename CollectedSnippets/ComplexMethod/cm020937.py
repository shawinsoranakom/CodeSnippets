async def test_availability(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    mock_nextdns_client: AsyncMock,
) -> None:
    """Ensure that we mark the entities unavailable correctly when service causes an error."""
    with patch("homeassistant.components.nextdns.PLATFORMS", [Platform.BINARY_SENSOR]):
        await init_integration(hass, mock_config_entry)

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    entity_ids = (entry.entity_id for entry in entity_entries)

    for entity_id in entity_ids:
        assert hass.states.get(entity_id).state != STATE_UNAVAILABLE

    mock_nextdns_client.connection_status.side_effect = ApiError("API Error")

    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for entity_id in entity_ids:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    mock_nextdns_client.connection_status.side_effect = None

    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for entity_id in entity_ids:
        assert hass.states.get(entity_id).state != STATE_UNAVAILABLE