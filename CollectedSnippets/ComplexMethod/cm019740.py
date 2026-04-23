async def test_ac_cover(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_get: AsyncMock,
    mock_update: AsyncMock,
) -> None:
    """Test cover platform."""

    await add_mock_config(hass)

    # Test Cover Zone Entity
    entity_id = "cover.myauto_zone_y"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.OPEN
    assert state.attributes.get("device_class") == CoverDeviceClass.DAMPER
    assert state.attributes.get("current_position") == 100

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac3-z01"

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: [entity_id], ATTR_POSITION: 50},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: [entity_id], ATTR_POSITION: 0},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test controlling multiple Cover Zone Entity
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {
            ATTR_ENTITY_ID: [
                "cover.myauto_zone_y",
                "cover.myauto_zone_z",
            ]
        },
        blocking=True,
    )
    assert len(mock_update.mock_calls) == 2
    mock_update.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {
            ATTR_ENTITY_ID: [
                "cover.myauto_zone_y",
                "cover.myauto_zone_z",
            ]
        },
        blocking=True,
    )

    assert len(mock_update.mock_calls) == 2