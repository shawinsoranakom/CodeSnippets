async def test_entity_already_in_progress(
    hass: HomeAssistant,
    mock_update_entities: list[MockUpdateEntity],
    caplog: pytest.LogCaptureFixture,
    entity_id: str,
    expected_display_precision: int,
    expected_update_percentage: float,
) -> None:
    """Test update install already in progress."""
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_DISPLAY_PRECISION] == expected_display_precision
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert state.attributes[ATTR_IN_PROGRESS] is True
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] == expected_update_percentage

    with pytest.raises(
        HomeAssistantError,
        match="Update installation already in progress for",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    # Check update percentage is suppressed when in_progress is False
    entity = next(
        entity for entity in mock_update_entities if entity.entity_id == entity_id
    )
    entity._attr_in_progress = False
    entity.async_write_ha_state()
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None