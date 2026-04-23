async def test_setup_platform_and_reload(hass: HomeAssistant, tmp_path: Path) -> None:
    """Test service setup and reload."""
    get_service_called = Mock()

    async def async_get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"a": 1, "b": 2}
        return NotificationService(hass, targetlist, "testnotify")

    async def async_get_service2(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get legacy notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"c": 3, "d": 4}
        return NotificationService(hass, targetlist, "testnotify2")

    # Mock first platform
    mock_notify_platform(
        hass, tmp_path, "testnotify", async_get_service=async_get_service
    )

    # Initialize a second platform testnotify2
    mock_notify_platform(
        hass, tmp_path, "testnotify2", async_get_service=async_get_service2
    )

    # Setup the testnotify platform
    await async_setup_component(
        hass, "notify", {"notify": [{"platform": "testnotify"}]}
    )
    await hass.async_block_till_done()
    assert hass.services.has_service("testnotify", SERVICE_RELOAD)
    assert hass.services.has_service(notify.DOMAIN, "testnotify_a")
    assert hass.services.has_service(notify.DOMAIN, "testnotify_b")
    assert get_service_called.call_count == 1
    assert get_service_called.call_args[0][0] == {"platform": "testnotify"}
    assert get_service_called.call_args[0][1] is None
    get_service_called.reset_mock()

    # Setup the second testnotify2 platform dynamically
    await async_load_platform(
        hass,
        "notify",
        "testnotify2",
        {},
        hass_config={"notify": [{"platform": "testnotify"}]},
    )
    await hass.async_block_till_done()
    assert hass.services.has_service("testnotify2", SERVICE_RELOAD)
    assert hass.services.has_service(notify.DOMAIN, "testnotify2_c")
    assert hass.services.has_service(notify.DOMAIN, "testnotify2_d")
    assert get_service_called.call_count == 1
    assert get_service_called.call_args[0][0] == {}
    assert get_service_called.call_args[0][1] == {}
    get_service_called.reset_mock()

    # Perform a reload
    new_yaml_config_file = tmp_path / "configuration.yaml"
    new_yaml_config = yaml.dump({"notify": [{"platform": "testnotify"}]})
    new_yaml_config_file.write_text(new_yaml_config)

    with patch.object(hass_config, "YAML_CONFIG_FILE", new_yaml_config_file):
        await hass.services.async_call(
            "testnotify",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.services.async_call(
            "testnotify2",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Check if the notify services from setup still exist
    assert hass.services.has_service(notify.DOMAIN, "testnotify_a")
    assert hass.services.has_service(notify.DOMAIN, "testnotify_b")
    assert get_service_called.call_count == 1
    assert get_service_called.call_args[0][0] == {"platform": "testnotify"}
    assert get_service_called.call_args[0][1] is None

    # Check if the dynamically notify services from setup were removed
    assert not hass.services.has_service(notify.DOMAIN, "testnotify2_c")
    assert not hass.services.has_service(notify.DOMAIN, "testnotify2_d")