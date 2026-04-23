async def test_entity_with_backup_support(
    hass: HomeAssistant,
    mock_update_entities: list[MockUpdateEntity],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test update entity with backup support."""
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    # This entity support backing up before install the update
    state = hass.states.get("update.update_backup")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"

    # Without a backup
    await hass.services.async_call(
        DOMAIN,
        SERVICE_INSTALL,
        {
            ATTR_BACKUP: False,
            ATTR_ENTITY_ID: "update.update_backup",
        },
        blocking=True,
    )

    state = hass.states.get("update.update_backup")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.1"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert "Creating backup before installing update" not in caplog.text
    assert "Installed latest update" in caplog.text

    # Specific version, do create a backup this time
    await hass.services.async_call(
        DOMAIN,
        SERVICE_INSTALL,
        {
            ATTR_BACKUP: True,
            ATTR_VERSION: "0.9.8",
            ATTR_ENTITY_ID: "update.update_backup",
        },
        blocking=True,
    )

    # This entity support backing up before install the update
    state = hass.states.get("update.update_backup")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "0.9.8"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert "Creating backup before installing update" in caplog.text
    assert "Installed update with version: 0.9.8" in caplog.text