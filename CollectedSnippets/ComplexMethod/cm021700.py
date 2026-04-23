async def test_entity_with_updates_available(
    hass: HomeAssistant,
    mock_update_entities: list[MockUpdateEntity],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test basic update entity with updates available."""
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    # Entity has an update available
    state = hass.states.get("update.update_available")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert state.attributes[ATTR_SKIPPED_VERSION] is None

    # Skip skip the update
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SKIP,
        {ATTR_ENTITY_ID: "update.update_available"},
        blocking=True,
    )

    # The state should have changed to off, skipped version should be set
    state = hass.states.get("update.update_available")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert state.attributes[ATTR_SKIPPED_VERSION] == "1.0.1"

    # Even though skipped, we can still update if we want to
    await hass.services.async_call(
        DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: "update.update_available"},
        blocking=True,
    )

    # The state should have changed to off, skipped version should be set
    state = hass.states.get("update.update_available")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.1"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert state.attributes[ATTR_SKIPPED_VERSION] is None
    assert "Installed latest update" in caplog.text