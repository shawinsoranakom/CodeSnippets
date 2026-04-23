async def async_migrate_entry(hass: HomeAssistant, entry: TVTrainConfigEntry) -> bool:
    """Migrate config entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version > 2:
        # This means the user has downgraded from a future version
        return False

    if entry.version == 1:
        if entry.minor_version == 1:
            # Remove unique id
            hass.config_entries.async_update_entry(
                entry, unique_id=None, minor_version=2
            )

        # Change from station names to station signatures
        try:
            web_session = async_get_clientsession(hass)
            train_api = TrafikverketTrain(web_session, entry.data[CONF_API_KEY])
            from_stations = await train_api.async_search_train_stations(
                entry.data[CONF_FROM]
            )
            to_stations = await train_api.async_search_train_stations(
                entry.data[CONF_TO]
            )
        except InvalidAuthentication as error:
            raise ConfigEntryAuthFailed from error
        except NoTrainStationFound as error:
            _LOGGER.error(
                "Migration failed as no train station found with provided name %s",
                str(error),
            )
            return False
        except UnknownError as error:
            _LOGGER.error("Unknown error occurred during validation %s", str(error))
            return False
        except Exception as error:  # noqa: BLE001
            _LOGGER.error("Unknown exception occurred during validation %s", str(error))
            return False

        if len(from_stations) > 1 or len(to_stations) > 1:
            _LOGGER.error(
                "Migration failed as more than one station found with provided name"
            )
            return False

        new_data = entry.data.copy()
        new_data[CONF_FROM] = from_stations[0].signature
        new_data[CONF_TO] = to_stations[0].signature

        hass.config_entries.async_update_entry(
            entry, data=new_data, version=2, minor_version=1
        )

    _LOGGER.debug(
        "Migration to version %s.%s successful",
        entry.version,
        entry.minor_version,
    )

    return True