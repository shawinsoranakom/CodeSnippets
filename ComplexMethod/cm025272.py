async def _initialize_webhook(
    hass: HomeAssistant,
    entry: SwitchbotCloudConfigEntry,
    api: SwitchBotAPI,
    coordinators_by_id: dict[str, SwitchBotCoordinator],
) -> None:
    """Initialize webhook if needed."""
    if any(
        coordinator.manageable_by_webhook()
        for coordinator in coordinators_by_id.values()
    ):
        if CONF_WEBHOOK_ID not in entry.data:
            new_data = entry.data.copy()
            if CONF_WEBHOOK_ID not in new_data:
                # create new id and new conf
                new_data[CONF_WEBHOOK_ID] = webhook.async_generate_id()

            hass.config_entries.async_update_entry(entry, data=new_data)

        # register webhook
        webhook_name = ENTRY_TITLE
        if entry.title != ENTRY_TITLE:
            webhook_name = f"{ENTRY_TITLE} {entry.title}"

        with contextlib.suppress(Exception):
            webhook.async_register(
                hass,
                DOMAIN,
                webhook_name,
                entry.data[CONF_WEBHOOK_ID],
                _create_handle_webhook(coordinators_by_id),
            )

        webhook_url = webhook.async_generate_url(
            hass,
            entry.data[CONF_WEBHOOK_ID],
        )
        # check if webhook is configured in switchbot cloud

        try:
            check_webhook_result = None
            with contextlib.suppress(Exception):
                check_webhook_result = await api.get_webook_configuration()

            actual_webhook_urls = (
                check_webhook_result["urls"]
                if check_webhook_result and "urls" in check_webhook_result
                else []
            )
            need_add_webhook = (
                len(actual_webhook_urls) == 0 or webhook_url not in actual_webhook_urls
            )
            need_clean_previous_webhook = (
                len(actual_webhook_urls) > 0 and webhook_url not in actual_webhook_urls
            )

            if need_clean_previous_webhook:
                # it seems is impossible to register multiple webhook.
                # So, if webhook already exists, we delete it
                await api.delete_webhook(actual_webhook_urls[0])
                _LOGGER.debug(
                    "Deleted previous Switchbot cloud webhook url: %s",
                    actual_webhook_urls[0],
                )

            if need_add_webhook:
                # call api for register webhookurl
                await api.setup_webhook(webhook_url)
                _LOGGER.debug(
                    "Registered Switchbot cloud webhook at hass: %s", webhook_url
                )

            for coordinator in coordinators_by_id.values():
                coordinator.webhook_subscription_listener(True)

            _LOGGER.debug("Registered Switchbot cloud webhook at: %s", webhook_url)
        except SwitchBotDeviceOfflineError as e:
            _LOGGER.error("Failed to connect Switchbot cloud device: %s", e)
        except SwitchBotConnectionError as e:
            _LOGGER.error("Failed to connect Switchbot cloud device: %s", e)