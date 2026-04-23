async def test_battery_pack_filtering(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_indevolt: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that battery pack sensors are filtered based on SN availability."""

    # Mock battery pack data - only first two packs have SNs
    mock_indevolt.fetch_data.return_value = {
        "9032": "BAT001",
        "9051": "BAT002",
        "9070": None,
        "9165": "",
        "9218": None,
    }

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Get all sensor entities
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Verify sensors for packs 1 and 2 exist (with SNs)
    pack1_sensors = [
        e
        for e in entity_entries
        if any(key in e.unique_id for key in ("9032", "9016", "9030", "9020", "19173"))
    ]
    pack2_sensors = [
        e
        for e in entity_entries
        if any(key in e.unique_id for key in ("9051", "9035", "9049", "9039", "19174"))
    ]

    assert len(pack1_sensors) == 5
    assert len(pack2_sensors) == 5

    # Verify sensors for packs 3, 4, and 5 don't exist (no SNs)
    pack3_sensors = [
        e
        for e in entity_entries
        if any(key in e.unique_id for key in ("9070", "9054", "9068", "9058", "19175"))
    ]
    pack4_sensors = [
        e
        for e in entity_entries
        if any(key in e.unique_id for key in ("9165", "9149", "9163", "9153", "19176"))
    ]
    pack5_sensors = [
        e
        for e in entity_entries
        if any(key in e.unique_id for key in ("9218", "9202", "9216", "9206", "19177"))
    ]

    assert len(pack3_sensors) == 0
    assert len(pack4_sensors) == 0
    assert len(pack5_sensors) == 0