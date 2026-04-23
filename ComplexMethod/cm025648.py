async def async_setup_entry(hass: HomeAssistant, entry: NetatmoConfigEntry) -> bool:
    """Set up Netatmo from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    # Set unique id if non was set (migration)
    if not entry.unique_id:
        hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)

    session = OAuth2Session(hass, entry, implementation)
    try:
        await session.async_ensure_token_valid()
    except OAuth2TokenRequestReauthError as ex:
        raise ConfigEntryAuthFailed("Token not valid, trigger renewal") from ex
    except (OAuth2TokenRequestError, ClientError) as ex:
        raise ConfigEntryNotReady from ex

    required_scopes = api.get_api_scopes(entry.data["auth_implementation"])
    if not (set(session.token["scope"]) & set(required_scopes)):
        _LOGGER.warning(
            "Session is missing scopes: %s",
            set(required_scopes) - set(session.token["scope"]),
        )
        raise ConfigEntryAuthFailed("Token scope not valid, trigger renewal")

    auth = api.AsyncConfigEntryNetatmoAuth(
        aiohttp_client.async_get_clientsession(hass), session
    )

    data_handler = NetatmoDataHandler(hass, entry, auth)
    entry.runtime_data = data_handler
    await data_handler.async_setup()

    async def unregister_webhook(
        _: Any,
    ) -> None:
        if CONF_WEBHOOK_ID not in entry.data:
            return
        _LOGGER.debug("Unregister Netatmo webhook (%s)", entry.data[CONF_WEBHOOK_ID])
        async_dispatcher_send(
            hass,
            f"signal-{DOMAIN}-webhook-None",
            {"type": "None", "data": {WEBHOOK_PUSH_TYPE: WEBHOOK_DEACTIVATION}},
        )
        webhook_unregister(hass, entry.data[CONF_WEBHOOK_ID])
        try:
            await entry.runtime_data.auth.async_dropwebhook()
        except pyatmo.ApiError:
            _LOGGER.debug(
                "No webhook to be dropped for %s", entry.data[CONF_WEBHOOK_ID]
            )

    async def register_webhook(
        _: Any,
    ) -> None:
        if CONF_WEBHOOK_ID not in entry.data:
            data = {**entry.data, CONF_WEBHOOK_ID: secrets.token_hex()}
            hass.config_entries.async_update_entry(entry, data=data)

        if cloud.async_active_subscription(hass):
            webhook_url = await async_cloudhook_generate_url(hass, entry)
        else:
            webhook_url = webhook_generate_url(hass, entry.data[CONF_WEBHOOK_ID])

        if entry.data[
            "auth_implementation"
        ] == cloud.DOMAIN and not webhook_url.startswith("https://"):
            _LOGGER.warning(
                "Webhook not registered - "
                "https and port 443 is required to register the webhook"
            )
            return

        webhook_register(
            hass,
            DOMAIN,
            "Netatmo",
            entry.data[CONF_WEBHOOK_ID],
            async_handle_webhook,
        )

        try:
            await entry.runtime_data.auth.async_addwebhook(webhook_url)
            _LOGGER.debug("Register Netatmo webhook: %s", webhook_url)
        except pyatmo.ApiError as err:
            _LOGGER.error("Error during webhook registration - %s", err)
        else:
            entry.async_on_unload(
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, unregister_webhook)
            )

    async def manage_cloudhook(state: cloud.CloudConnectionState) -> None:
        if state is cloud.CloudConnectionState.CLOUD_CONNECTED:
            await register_webhook(None)

        if state is cloud.CloudConnectionState.CLOUD_DISCONNECTED:
            await unregister_webhook(None)
            entry.async_on_unload(async_call_later(hass, 30, register_webhook))

    if cloud.async_active_subscription(hass):
        if cloud.async_is_connected(hass):
            await register_webhook(None)
        entry.async_on_unload(
            cloud.async_listen_connection_change(hass, manage_cloudhook)
        )
    else:
        entry.async_on_unload(async_at_started(hass, register_webhook))

    hass.services.async_register(DOMAIN, "register_webhook", register_webhook)
    hass.services.async_register(DOMAIN, "unregister_webhook", unregister_webhook)

    entry.async_on_unload(entry.add_update_listener(async_config_entry_updated))

    return True