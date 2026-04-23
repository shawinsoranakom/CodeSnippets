async def test_entity_with_specific_version(
    hass: HomeAssistant,
    mock_update_entities: list[MockUpdateEntity],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test update entity that support specific version."""
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get("update.update_specific_version")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.0"

    # Update to a specific version
    await hass.services.async_call(
        DOMAIN,
        SERVICE_INSTALL,
        {ATTR_VERSION: "0.9.9", ATTR_ENTITY_ID: "update.update_specific_version"},
        blocking=True,
    )

    # Version has changed, state should be on as there is an update available
    state = hass.states.get("update.update_specific_version")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "0.9.9"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.0"
    assert "Installed update with version: 0.9.9" in caplog.text

    # Update back to the latest version
    await hass.services.async_call(
        DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: "update.update_specific_version"},
        blocking=True,
    )

    state = hass.states.get("update.update_specific_version")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.0"
    assert "Installed latest update" in caplog.text

    # This entity does not support doing a backup before upgrade
    with pytest.raises(HomeAssistantError, match="Backup is not supported for"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INSTALL,
            {
                ATTR_VERSION: "0.9.9",
                ATTR_BACKUP: True,
                ATTR_ENTITY_ID: "update.update_specific_version",
            },
            blocking=True,
        )