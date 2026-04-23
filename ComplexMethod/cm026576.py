async def _async_setup_graphql_sensors(
    hass: HomeAssistant,
    entry: TibberConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tibber sensor."""

    tibber_connection = await entry.runtime_data.async_get_client(hass)

    entity_registry = er.async_get(hass)

    coordinator = entry.runtime_data.data_coordinator
    price_coordinator = entry.runtime_data.price_coordinator
    entities: list[TibberSensor] = []
    for home in tibber_connection.get_homes(only_active=False):
        try:
            await home.update_info()
        except TimeoutError as err:
            _LOGGER.error("Timeout connecting to Tibber home: %s ", err)
            raise PlatformNotReady from err
        except (
            RetryableHttpExceptionError,
            FatalHttpExceptionError,
            aiohttp.ClientError,
        ) as err:
            _LOGGER.error("Error connecting to Tibber home: %s ", err)
            raise PlatformNotReady from err

        if price_coordinator is not None and home.has_active_subscription:
            entities.append(TibberSensorElPrice(price_coordinator, home))
        if coordinator is not None and home.has_active_subscription:
            entities.extend(
                TibberDataSensor(home, coordinator, entity_description)
                for entity_description in SENSORS
            )

        if home.has_real_time_consumption:
            entity_creator = TibberRtEntityCreator(
                async_add_entities, home, entity_registry
            )
            await home.rt_subscribe(
                TibberRtDataCoordinator(
                    hass,
                    entry,
                    entity_creator.add_sensors,
                    home,
                ).async_set_updated_data
            )

    async_add_entities(entities)