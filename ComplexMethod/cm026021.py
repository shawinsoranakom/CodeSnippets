async def async_migrate_entry(
    hass: HomeAssistant, config_entry: GrowattConfigEntry
) -> bool:
    """Migrate old config entries.

    Migration from version 1.0 to 1.1:
    - Resolves DEFAULT_PLANT_ID (legacy value "0") to actual plant_id
    - Only applies to Classic API (username/password authentication)
    - Caches the logged-in API instance to avoid growatt server API rate limiting

    Rate Limiting Workaround:
    The Growatt Classic API rate-limits individual endpoints (login, plant_list,
    device_list) with 5-minute windows. Without caching, the sequence would be:
        Migration: login() → plant_list()
        Setup:     login() → device_list()
    This results in 2 login() calls within seconds, triggering rate limits.

    By caching the API instance (which contains the authenticated session), we
    achieve:
        Migration: login() → plant_list() → [cache API instance]
        Setup:     [reuse cached API] → device_list()
    This reduces to just 1 login() call during the migration+setup cycle and prevent account lockout.
    """
    _LOGGER.debug(
        "Migrating config entry from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    # Migrate from version 1.0 to 1.1
    if config_entry.version == 1 and config_entry.minor_version < 1:
        config = config_entry.data

        # First, ensure auth_type field exists (legacy config entry migration)
        # This handles config entries created before auth_type was introduced
        if CONF_AUTH_TYPE not in config:
            new_data = dict(config_entry.data)
            # Detect auth type based on which fields are present
            if CONF_TOKEN in config:
                new_data[CONF_AUTH_TYPE] = AUTH_API_TOKEN
                hass.config_entries.async_update_entry(config_entry, data=new_data)
                config = config_entry.data
                _LOGGER.debug("Added auth_type field to V1 API config entry")
            elif CONF_USERNAME in config:
                new_data[CONF_AUTH_TYPE] = AUTH_PASSWORD
                hass.config_entries.async_update_entry(config_entry, data=new_data)
                config = config_entry.data
                _LOGGER.debug("Added auth_type field to Classic API config entry")
            else:
                # Config entry has no auth fields - this is invalid but migration
                # should still succeed. Setup will fail later with a clearer error.
                _LOGGER.warning(
                    "Config entry has no authentication fields. "
                    "Setup will fail until the integration is reconfigured"
                )

        # Handle DEFAULT_PLANT_ID resolution
        if config.get(CONF_PLANT_ID) == DEFAULT_PLANT_ID:
            # V1 API should never have DEFAULT_PLANT_ID (plant selection happens in config flow)
            # If it does, this indicates a corrupted config entry
            if config.get(CONF_AUTH_TYPE) == AUTH_API_TOKEN:
                _LOGGER.error(
                    "V1 API config entry has DEFAULT_PLANT_ID, which indicates a "
                    "corrupted configuration. Please reconfigure the integration"
                )
                return False

            # Classic API with DEFAULT_PLANT_ID - resolve to actual plant_id
            if config.get(CONF_AUTH_TYPE) == AUTH_PASSWORD:
                username = config.get(CONF_USERNAME)
                password = config.get(CONF_PASSWORD)
                url = config.get(CONF_URL, DEFAULT_URL)

                if not username or not password:
                    # Credentials missing - cannot migrate
                    _LOGGER.error(
                        "Cannot migrate DEFAULT_PLANT_ID due to missing credentials"
                    )
                    return False

                try:
                    # Create API instance and login
                    api, login_response = await _create_api_and_login(
                        hass, username, password, url
                    )

                    # Resolve DEFAULT_PLANT_ID to actual plant_id
                    plant_info = await hass.async_add_executor_job(
                        api.plant_list, login_response["user"]["id"]
                    )
                except (ConfigEntryError, RequestException, JSONDecodeError) as ex:
                    # API failure during migration - return False to retry later
                    _LOGGER.error(
                        "Failed to resolve plant_id during migration: %s. "
                        "Migration will retry on next restart",
                        ex,
                    )
                    return False

                if not plant_info or "data" not in plant_info or not plant_info["data"]:
                    _LOGGER.error(
                        "No plants found for this account. "
                        "Migration will retry on next restart"
                    )
                    return False

                first_plant_id = plant_info["data"][0]["plantId"]

                # Update config entry with resolved plant_id
                new_data = dict(config_entry.data)
                new_data[CONF_PLANT_ID] = first_plant_id
                hass.config_entries.async_update_entry(
                    config_entry, data=new_data, minor_version=1
                )

                # Cache the logged-in API instance for reuse in async_setup_entry()
                hass.data.setdefault(DOMAIN, {})
                hass.data[DOMAIN][f"{CACHED_API_KEY}{config_entry.entry_id}"] = api

                _LOGGER.info(
                    "Migrated config entry to use specific plant_id '%s'",
                    first_plant_id,
                )
        else:
            # No DEFAULT_PLANT_ID to resolve, just bump version
            hass.config_entries.async_update_entry(config_entry, minor_version=1)

        _LOGGER.debug("Migration completed to version %s.%s", config_entry.version, 1)

    return True