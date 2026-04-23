async def test_polling_platform_message_text_update(
    hass: HomeAssistant,
    mock_polling_config_entry: MockConfigEntry,
    update_message_text,
    mock_external_calls: None,
) -> None:
    """Provide the `BaseTelegramBot.update_handler` with an `Update` and assert fired `telegram_text` event."""
    events = async_capture_events(hass, "telegram_text")

    with patch(
        "homeassistant.components.telegram_bot.polling.ApplicationBuilder"
    ) as application_builder_class:
        # Set up the integration with the polling platform inside the patch context manager.
        application = (
            application_builder_class.return_value.bot.return_value.build.return_value
        )
        application.updater.start_polling = AsyncMock()
        application.updater.stop = AsyncMock()
        application.initialize = AsyncMock()
        application.start = AsyncMock()
        application.stop = AsyncMock()
        application.shutdown = AsyncMock()

        mock_polling_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_polling_config_entry.entry_id)
        await hass.async_block_till_done()

        # Then call the callback and assert events fired.
        handler = application.add_handler.call_args[0][0]
        handle_update_callback = handler.callback

        # Create Update object using library API.
        application.bot.defaults.tzinfo = None
        update = Update.de_json(update_message_text, application.bot)

        # handle_update_callback == BaseTelegramBot.update_handler
        await handle_update_callback(update, None)

    # Make sure event has fired
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["text"] == update_message_text["message"]["text"]
    assert (
        events[0].data["bot"]["config_entry_id"] == mock_polling_config_entry.entry_id
    )
    assert events[0].data["bot"]["id"] == 123456
    assert events[0].data["bot"]["first_name"] == "Testbot"
    assert events[0].data["bot"]["last_name"] == "mock last name"
    assert events[0].data["bot"]["username"] == "mock_bot"

    assert isinstance(events[0].context, Context)