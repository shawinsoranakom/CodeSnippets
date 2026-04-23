async def test_select_entity(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test the creation and state of the diffuser select entity."""
    config_entry = mock_config_entry(unique_id="select_test")
    diffuser = mock_diffuser(hublot="lot123", room_size_square_meter=60)
    await init_integration(hass, config_entry, [diffuser])

    state = hass.states.get("select.genie_room_size")
    assert state
    assert state.state == str(diffuser.room_size_square_meter)
    assert state.attributes[ATTR_OPTIONS] == ["15", "30", "60", "100"]

    entry = entity_registry.async_get("select.genie_room_size")
    assert entry
    assert entry.unique_id == f"{diffuser.hublot}-room_size_square_meter"
    assert entry.unit_of_measurement == UnitOfArea.SQUARE_METERS
    assert entry.entity_category == EntityCategory.CONFIG