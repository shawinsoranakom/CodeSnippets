async def async_setup_entry(hass: HomeAssistant, entry: PowerwallConfigEntry) -> bool:
    """Set up Tesla Powerwall from a config entry."""
    ip_address: str = entry.data[CONF_IP_ADDRESS]

    password: str | None = entry.data.get(CONF_PASSWORD)

    cookie_jar: CookieJar = CookieJar(unsafe=True)
    use_auth_cookie: bool = False
    # Try to reuse the auth cookie
    auth_cookie_value: str | None = entry.data.get(CONFIG_ENTRY_COOKIE)
    if auth_cookie_value:
        cookie_jar.update_cookies(
            {AUTH_COOKIE_KEY: auth_cookie_value},
            URL(f"http://{ip_address}"),
        )
        _LOGGER.debug("Using existing auth cookie")
        use_auth_cookie = True

    http_session = async_create_clientsession(
        hass, verify_ssl=False, cookie_jar=cookie_jar
    )

    async with AsyncExitStack() as stack:
        power_wall = Powerwall(ip_address, http_session=http_session, verify_ssl=False)
        stack.push_async_callback(power_wall.close)

        for tries in range(2):
            try:
                base_info = await _login_and_fetch_base_info(
                    power_wall, ip_address, password, use_auth_cookie
                )

                # Cancel closing power_wall on success
                stack.pop_all()
                break
            except (TimeoutError, PowerwallUnreachableError) as err:
                raise ConfigEntryNotReady from err
            except MissingAttributeError as err:
                # The error might include some important information about what exactly changed.
                _LOGGER.error("The powerwall api has changed: %s", str(err))
                persistent_notification.async_create(
                    hass, API_CHANGED_ERROR_BODY, API_CHANGED_TITLE
                )
                return False
            except AccessDeniedError as err:
                if use_auth_cookie and tries == 0:
                    _LOGGER.debug(
                        "Authentication failed with cookie, retrying with password"
                    )
                    use_auth_cookie = False
                    continue
                _LOGGER.debug("Authentication failed", exc_info=err)
                raise ConfigEntryAuthFailed from err
            except ApiError as err:
                raise ConfigEntryNotReady from err

    gateway_din = base_info.gateway_din
    if entry.unique_id is not None and is_ip_address(entry.unique_id):
        hass.config_entries.async_update_entry(entry, unique_id=gateway_din)

    runtime_data = PowerwallRuntimeData(
        api_changed=False,
        base_info=base_info,
        coordinator=None,
        api_instance=power_wall,
    )

    manager = PowerwallDataManager(
        hass,
        power_wall,
        cookie_jar,
        entry,
        ip_address,
        password,
        runtime_data,
    )
    manager.save_auth_cookie()

    coordinator = PowerwallUpdateCoordinator(hass, entry, manager)

    await coordinator.async_config_entry_first_refresh()

    runtime_data[POWERWALL_COORDINATOR] = coordinator

    entry.runtime_data = runtime_data

    await async_migrate_entity_unique_ids(hass, entry, base_info)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True