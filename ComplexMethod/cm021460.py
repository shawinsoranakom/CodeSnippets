async def test_legacy_calendars(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_mealie_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that only legacy calendars are created for Mealie versions prior to 3.7.0."""

    mock_mealie_client.get_about.return_value = About(version="v3.6.0")

    with patch("homeassistant.components.mealie.PLATFORMS", [Platform.CALENDAR]):
        await setup_integration(hass, mock_config_entry)

    assert entity_registry.async_get("calendar.mealie_dessert") is None
    assert entity_registry.async_get("calendar.mealie_drink") is None
    assert entity_registry.async_get("calendar.mealie_snack") is None
    assert entity_registry.async_get("calendar.mealie_breakfast") is not None
    assert entity_registry.async_get("calendar.mealie_lunch") is not None
    assert entity_registry.async_get("calendar.mealie_dinner") is not None
    assert entity_registry.async_get("calendar.mealie_side") is not None