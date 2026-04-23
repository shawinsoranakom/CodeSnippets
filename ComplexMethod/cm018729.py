async def test_turn_on_off_intent_cover(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test HassTurnOn/Off intent on cover domains."""
    assert await async_setup_component(hass, "intent", {})

    cover = entity_registry.async_get_or_create("cover", "test", "cover_uid")

    hass.states.async_set(cover.entity_id, "closed")
    open_calls = async_mock_service(hass, "cover", SERVICE_OPEN_COVER)
    close_calls = async_mock_service(hass, "cover", SERVICE_CLOSE_COVER)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": cover.entity_id}}
    )

    assert len(open_calls) == 1
    call = open_calls[0]
    assert call.domain == "cover"
    assert call.service == SERVICE_OPEN_COVER
    assert call.data == {"entity_id": cover.entity_id}

    await intent.async_handle(
        hass, "test", "HassTurnOff", {"name": {"value": cover.entity_id}}
    )

    assert len(close_calls) == 1
    call = close_calls[0]
    assert call.domain == "cover"
    assert call.service == SERVICE_CLOSE_COVER
    assert call.data == {"entity_id": cover.entity_id}