async def test_validating_mfa_counter(hass: HomeAssistant) -> None:
    """Test counter will move only after generate code."""
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})
    await notify_auth_module.async_setup_user(
        "test-user", {"counter": 0, "notify_service": "dummy"}
    )
    async_mock_service(hass, "notify", "dummy")

    assert notify_auth_module._user_settings
    notify_setting = list(notify_auth_module._user_settings.values())[0]
    init_count = notify_setting.counter
    assert init_count is not None

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        await notify_auth_module.async_initialize_login_mfa_step("test-user")

    notify_setting = list(notify_auth_module._user_settings.values())[0]
    after_generate_count = notify_setting.counter
    assert after_generate_count != init_count

    with patch("pyotp.HOTP.verify", return_value=True):
        assert await notify_auth_module.async_validate("test-user", {"code": MOCK_CODE})

    notify_setting = list(notify_auth_module._user_settings.values())[0]
    assert after_generate_count == notify_setting.counter

    with patch("pyotp.HOTP.verify", return_value=False):
        assert (
            await notify_auth_module.async_validate("test-user", {"code": MOCK_CODE})
            is False
        )

    notify_setting = list(notify_auth_module._user_settings.values())[0]
    assert after_generate_count == notify_setting.counter