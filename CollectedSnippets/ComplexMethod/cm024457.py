async def setup_push_receiver(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, hass_admin_user: MockUser
) -> None:
    """Fixture that sets up a mocked push receiver."""
    push_url = "https://mobile-push.home-assistant.dev/push"

    now = datetime.now() + timedelta(hours=24)
    iso_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    aioclient_mock.post(
        push_url,
        json={
            "rateLimits": {
                "attempts": 1,
                "successful": 1,
                "errors": 0,
                "total": 1,
                "maximum": 150,
                "remaining": 149,
                "resetsAt": iso_time,
            }
        },
    )

    entry = MockConfigEntry(
        data={
            "app_data": {"push_token": "PUSH_TOKEN", "push_url": push_url},
            "app_id": "io.homeassistant.mobile_app",
            "app_name": "mobile_app tests",
            "app_version": "1.0",
            "device_id": "4d5e6f",
            "device_name": "Test",
            "manufacturer": "Home Assistant",
            "model": "mobile_app",
            "os_name": "Linux",
            "os_version": "5.0.6",
            "secret": "123abc",
            "supports_encryption": False,
            "user_id": hass_admin_user.id,
            "webhook_id": "mock-webhook_id",
        },
        domain=DOMAIN,
        source="registration",
        title="mobile_app test entry",
        version=1,
    )
    entry.add_to_hass(hass)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    loaded_late_entry = MockConfigEntry(
        data={
            "app_data": {"push_token": "PUSH_TOKEN2", "push_url": f"{push_url}2"},
            "app_id": "io.homeassistant.mobile_app",
            "app_name": "mobile_app tests",
            "app_version": "1.0",
            "device_id": "4d5e6f2",
            "device_name": "Loaded Late",
            "manufacturer": "Home Assistant",
            "model": "mobile_app",
            "os_name": "Linux",
            "os_version": "5.0.6",
            "secret": "123abc2",
            "supports_encryption": False,
            "user_id": "1a2b3c2",
            "webhook_id": "webhook_id_2",
        },
        domain=DOMAIN,
        source="registration",
        title="mobile_app 2 test entry",
        version=1,
    )
    loaded_late_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(loaded_late_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service("notify", "mobile_app_loaded_late")

    assert await hass.config_entries.async_remove(loaded_late_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service("notify", "mobile_app_test")
    assert not hass.services.has_service("notify", "mobile_app_loaded_late")

    loaded_late_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(loaded_late_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service("notify", "mobile_app_test")
    assert hass.services.has_service("notify", "mobile_app_loaded_late")