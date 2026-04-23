async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test integration setup from entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DSN: "http://public@example.com/1", CONF_ENVIRONMENT: "production"},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.sentry.AioHttpIntegration"
        ) as sentry_aiohttp_mock,
        patch(
            "homeassistant.components.sentry.SqlalchemyIntegration"
        ) as sentry_sqlalchemy_mock,
        patch(
            "homeassistant.components.sentry.LoggingIntegration"
        ) as sentry_logging_mock,
        patch("homeassistant.components.sentry.sentry_sdk") as sentry_mock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Test CONF_ENVIRONMENT is migrated to entry options
    assert CONF_ENVIRONMENT not in entry.data
    assert CONF_ENVIRONMENT in entry.options
    assert entry.options[CONF_ENVIRONMENT] == "production"

    assert sentry_logging_mock.call_count == 1
    sentry_logging_mock.assert_called_once_with(
        level=logging.WARNING, event_level=logging.ERROR
    )

    assert sentry_aiohttp_mock.call_count == 1
    assert sentry_sqlalchemy_mock.call_count == 1
    assert sentry_mock.init.call_count == 1

    call_args = sentry_mock.init.call_args[1]
    assert set(call_args) == {
        "dsn",
        "environment",
        "integrations",
        "release",
        "before_send",
    }
    assert call_args["dsn"] == "http://public@example.com/1"
    assert call_args["environment"] == "production"
    assert call_args["integrations"] == [
        sentry_logging_mock.return_value,
        sentry_aiohttp_mock.return_value,
        sentry_sqlalchemy_mock.return_value,
    ]
    assert call_args["release"] == current_version
    assert call_args["before_send"]