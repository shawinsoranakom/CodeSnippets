async def test_update(hass: HomeAssistant) -> None:
    """Test getting data from the mocked update entity."""
    update = UpdateEntity()
    update.hass = hass
    update.platform = MockEntityPlatform(hass)

    update._attr_installed_version = "1.0.0"
    update._attr_latest_version = "1.0.1"
    update._attr_release_summary = "Summary"
    update._attr_release_url = "https://example.com"
    update._attr_title = "Title"

    assert update.entity_category is EntityCategory.DIAGNOSTIC
    assert update.entity_picture == "/api/brands/integration/test_platform/icon.png"
    assert update.installed_version == "1.0.0"
    assert update.latest_version == "1.0.1"
    assert update.release_summary == "Summary"
    assert update.release_url == "https://example.com"
    assert update.title == "Title"
    assert update.in_progress is False
    assert update.state == STATE_ON
    assert update.state_attributes == {
        ATTR_AUTO_UPDATE: False,
        ATTR_DISPLAY_PRECISION: 0,
        ATTR_INSTALLED_VERSION: "1.0.0",
        ATTR_IN_PROGRESS: False,
        ATTR_LATEST_VERSION: "1.0.1",
        ATTR_RELEASE_SUMMARY: "Summary",
        ATTR_RELEASE_URL: "https://example.com",
        ATTR_SKIPPED_VERSION: None,
        ATTR_TITLE: "Title",
        ATTR_UPDATE_PERCENTAGE: None,
    }

    # Test no update available
    update._attr_installed_version = "1.0.0"
    update._attr_latest_version = "1.0.0"
    assert update.state is STATE_OFF

    # Test state becomes unknown if installed version is unknown
    update._attr_installed_version = None
    update._attr_latest_version = "1.0.0"
    assert update.state is None

    # Test state becomes unknown if latest version is unknown
    update._attr_installed_version = "1.0.0"
    update._attr_latest_version = None
    assert update.state is None

    # Test no update if new version is not an update
    update._attr_installed_version = "1.0.0"
    update._attr_latest_version = "0.9.0"
    assert update.state is STATE_OFF

    # Test update if new version is not considered a valid version
    update._attr_installed_version = "1.0.0"
    update._attr_latest_version = "awesome_update"
    assert update.state is STATE_ON

    # Test entity category becomes config when its possible to install
    update._attr_supported_features = UpdateEntityFeature.INSTALL
    assert update.entity_category is EntityCategory.CONFIG

    # UpdateEntityDescription was set
    update._attr_supported_features = 0
    update.entity_description = UpdateEntityDescription(key="F5 - Its very refreshing")
    assert update.device_class is None
    assert update.entity_category is EntityCategory.CONFIG
    del update.device_class
    update.entity_description = UpdateEntityDescription(
        key="F5 - Its very refreshing",
        device_class=UpdateDeviceClass.FIRMWARE,
        entity_category=None,
    )
    assert update.device_class is UpdateDeviceClass.FIRMWARE
    assert update.entity_category is None

    # Device class via attribute (override entity description)
    update._attr_device_class = None
    assert update.device_class is None
    update._attr_device_class = UpdateDeviceClass.FIRMWARE
    assert update.device_class is UpdateDeviceClass.FIRMWARE

    # Entity Attribute via attribute (override entity description)
    update._attr_entity_category = None
    assert update.entity_category is None
    update._attr_entity_category = EntityCategory.DIAGNOSTIC
    assert update.entity_category is EntityCategory.DIAGNOSTIC

    with pytest.raises(NotImplementedError):
        await update.async_install(version=None, backup=True)

    with pytest.raises(NotImplementedError):
        update.install(version=None, backup=False)

    update.install = MagicMock()
    await update.async_install(version="1.0.1", backup=True)

    assert update.install.called
    assert update.install.call_args[0][0] == "1.0.1"
    assert update.install.call_args[0][1] is True