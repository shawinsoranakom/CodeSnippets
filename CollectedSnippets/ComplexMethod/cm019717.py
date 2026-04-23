async def test_update_entity_installation_failure(
    hass: HomeAssistant, update_config_entry: ConfigEntry
) -> None:
    """Test installation failing during flashing."""
    assert await hass.config_entries.async_setup(update_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {"entity_id": TEST_UPDATE_ENTITY_ID},
        blocking=True,
    )

    state_before_install = hass.states.get(TEST_UPDATE_ENTITY_ID)
    assert state_before_install is not None
    assert state_before_install.state == "on"
    assert state_before_install.attributes["title"] == "EmberZNet"
    assert state_before_install.attributes["installed_version"] == "7.3.1.0"
    assert state_before_install.attributes["latest_version"] == "7.4.4.0"

    with (
        patch(
            "homeassistant.components.homeassistant_hardware.update.async_flash_silabs_firmware",
            side_effect=HomeAssistantError("Failed to flash firmware"),
        ),
        pytest.raises(HomeAssistantError, match="Failed to flash firmware"),
    ):
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": TEST_UPDATE_ENTITY_ID},
            blocking=True,
        )

    # After the firmware update fails, we can still try again
    state_after_install = hass.states.get(TEST_UPDATE_ENTITY_ID)
    assert state_after_install is not None
    assert state_after_install.state == "on"
    assert state_after_install.attributes["title"] == "EmberZNet"
    assert state_after_install.attributes["installed_version"] == "7.3.1.0"
    assert state_after_install.attributes["latest_version"] == "7.4.4.0"