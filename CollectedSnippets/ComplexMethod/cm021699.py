async def test_entity_with_no_install(
    hass: HomeAssistant,
    mock_update_entities: list[MockUpdateEntity],
) -> None:
    """Test entity with no updates."""
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    # Update is available
    state = hass.states.get("update.update_no_install")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"

    # Should not be able to install as the entity doesn't support that
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: "update.update_no_install"},
            blocking=True,
        )

    # Nothing changed
    state = hass.states.get("update.update_no_install")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert state.attributes[ATTR_SKIPPED_VERSION] is None

    # We can mark the update as skipped
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SKIP,
        {ATTR_ENTITY_ID: "update.update_no_install"},
        blocking=True,
    )

    state = hass.states.get("update.update_no_install")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert state.attributes[ATTR_SKIPPED_VERSION] == "1.0.1"

    # We can clear the skipped marker again
    await hass.services.async_call(
        DOMAIN,
        "clear_skipped",
        {ATTR_ENTITY_ID: "update.update_no_install"},
        blocking=True,
    )

    state = hass.states.get("update.update_no_install")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert state.attributes[ATTR_SKIPPED_VERSION] is None