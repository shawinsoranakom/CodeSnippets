async def test_setup(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_asyncsleepiq
) -> None:
    """Test for successfully setting up the SleepIQ platform."""
    entry = await setup_platform(hass, LIGHT_DOMAIN)

    assert len(entity_registry.entities) == 2

    entry = entity_registry.async_get(
        f"light.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_light_1"
    )
    assert entry
    assert entry.original_name == f"SleepNumber {BED_NAME} Light 1"
    assert entry.unique_id == f"{BED_ID}-light-1"

    entry = entity_registry.async_get(
        f"light.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_light_2"
    )
    assert entry
    assert entry.original_name == f"SleepNumber {BED_NAME} Light 2"
    assert entry.unique_id == f"{BED_ID}-light-2"