async def test_reload_notify(hass: HomeAssistant, tmp_path: Path) -> None:
    """Verify we can reload the notify service."""
    assert await async_setup_component(
        hass,
        "group",
        {},
    )
    await hass.async_block_till_done()

    await help_setup_notify(
        hass,
        tmp_path,
        {"service1": 1, "service2": 2},
        [
            {
                "name": "group_notify",
                "platform": "group",
                "services": [{"action": "test_service1"}],
            }
        ],
    )

    assert hass.services.has_service(notify.DOMAIN, "test_service1")
    assert hass.services.has_service(notify.DOMAIN, "test_service2")
    assert hass.services.has_service(notify.DOMAIN, "group_notify")

    yaml_path = get_fixture_path("configuration.yaml", "group")

    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            "group",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert hass.services.has_service(notify.DOMAIN, "test_service1")
    assert hass.services.has_service(notify.DOMAIN, "test_service2")
    assert not hass.services.has_service(notify.DOMAIN, "group_notify")
    assert hass.services.has_service(notify.DOMAIN, "new_group_notify")