async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Entur public transport sensor."""

    expand = config[CONF_EXPAND_PLATFORMS]
    line_whitelist = config[CONF_WHITELIST_LINES]
    name = config[CONF_NAME]
    show_on_map = config[CONF_SHOW_ON_MAP]
    stop_ids = config[CONF_STOP_IDS]
    omit_non_boarding = config[CONF_OMIT_NON_BOARDING]
    number_of_departures = config[CONF_NUMBER_OF_DEPARTURES]

    stops = [s for s in stop_ids if "StopPlace" in s]
    quays = [s for s in stop_ids if "Quay" in s]

    data = EnturPublicTransportData(
        API_CLIENT_NAME.format(str(randint(100000, 999999))),
        stops=stops,
        quays=quays,
        line_whitelist=line_whitelist,
        omit_non_boarding=omit_non_boarding,
        number_of_departures=number_of_departures,
        web_session=async_get_clientsession(hass),
    )

    if expand:
        await data.expand_all_quays()
    await data.update()

    proxy = EnturProxy(data)

    entities = []
    for place in data.all_stop_places_quays():
        try:
            given_name = f"{name} {data.get_stop_info(place).name}"
        except KeyError:
            given_name = f"{name} {place}"

        entities.append(
            EnturPublicTransportSensor(proxy, given_name, place, show_on_map)
        )

    async_add_entities(entities, True)