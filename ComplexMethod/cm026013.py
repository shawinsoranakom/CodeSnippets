async def async_setup_entry(hass: HomeAssistant, entry: NestConfigEntry) -> bool:
    """Set up Nest from a config entry with dispatch between old/new flows."""
    if DATA_SDM not in entry.data:
        hass.async_create_task(hass.config_entries.async_remove(entry.entry_id))
        return False

    if entry.unique_id != entry.data[CONF_PROJECT_ID]:
        hass.config_entries.async_update_entry(
            entry, unique_id=entry.data[CONF_PROJECT_ID]
        )

    auth = await api.new_auth(hass, entry)
    try:
        await auth.async_get_access_token()
    except OAuth2TokenRequestReauthError as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN, translation_key="reauth_required"
        ) from err
    except OAuth2TokenRequestError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="auth_server_error"
        ) from err
    except ClientError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="auth_client_error"
        ) from err

    subscriber = await api.new_subscriber(hass, entry, auth)
    if not subscriber:
        return False
    # Keep media for last N events in memory
    subscriber.cache_policy.event_cache_size = EVENT_MEDIA_CACHE_SIZE
    subscriber.cache_policy.fetch = True
    # Use disk backed event media store
    subscriber.cache_policy.store = await async_get_media_event_store(hass, subscriber)
    subscriber.cache_policy.transcoder = await async_get_transcoder(hass)

    # The device manager has a single change callback. When the change
    # callback is invoked, we update the DeviceListener with the current
    # set of devices which will notify any registered listeners with the
    # changes.
    update_callback = SignalUpdateCallback(hass, entry)
    subscriber.set_update_callback(update_callback.async_handle_event)
    try:
        unsub = await subscriber.start_async()
    except AuthException as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="reauth_required",
        ) from err
    except ConfigurationException as err:
        _LOGGER.error("Configuration error: %s", err)
        return False
    except SubscriberTimeoutException as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="subscriber_timeout",
        ) from err
    except SubscriberException as err:
        _LOGGER.error("Subscriber error: %s", err)
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="subscriber_error",
        ) from err

    try:
        device_manager = await subscriber.async_get_device_manager()
    except ApiException as err:
        unsub()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_api_error",
        ) from err

    @callback
    def on_hass_stop(_: Event) -> None:
        """Close connection when hass stops."""
        unsub()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)
    )

    update_callback.set_device_manager(device_manager)

    entry.async_on_unload(unsub)
    entry.runtime_data = NestData(
        subscriber=subscriber,
        device_manager=device_manager,
        register_devices_listener=update_callback.register_devices_listener,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True