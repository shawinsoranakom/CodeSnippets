async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the CityBikes platform."""
    if PLATFORM not in hass.data:
        hass.data[PLATFORM] = {MONITORED_NETWORKS: {}}

    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    network_id = config.get(CONF_NETWORK)
    stations_list = set(config.get(CONF_STATIONS_LIST, []))
    radius = config.get(CONF_RADIUS, 0)
    name = config[CONF_NAME]
    if hass.config.units is US_CUSTOMARY_SYSTEM:
        radius = DistanceConverter.convert(
            radius, UnitOfLength.FEET, UnitOfLength.METERS
        )

    client = CitybikesClient(user_agent=HA_USER_AGENT, timeout=REQUEST_TIMEOUT)
    hass.data[PLATFORM][DATA_CLIENT] = client

    async def _async_close_client(event):
        await client.close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_CLOSE, _async_close_client)

    # Create a single instance of CityBikesNetworks.
    networks = hass.data.setdefault(CITYBIKES_NETWORKS, CityBikesNetworks(hass))

    if not network_id:
        network_id = await networks.get_closest_network_id(latitude, longitude)

    if network_id not in hass.data[PLATFORM][MONITORED_NETWORKS]:
        network = CityBikesNetwork(hass, network_id)
        hass.data[PLATFORM][MONITORED_NETWORKS][network_id] = network
        hass.async_create_task(network.async_refresh())
        async_track_time_interval(hass, network.async_refresh, SCAN_INTERVAL)
    else:
        network = hass.data[PLATFORM][MONITORED_NETWORKS][network_id]

    await network.ready.wait()

    devices = []
    for station in network.stations:
        dist = location_util.distance(
            latitude, longitude, station.latitude, station.longitude
        )
        station_id = station.id
        station_uid = str(station.extra.get(ATTR_UID, ""))

        if radius > dist or stations_list.intersection((station_id, station_uid)):
            if name:
                uid = f"{network.network_id}_{name}_{station_id}"
            else:
                uid = f"{network.network_id}_{station_id}"
            entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, uid, hass=hass)
            devices.append(CityBikesStation(network, station_id, entity_id))

    async_add_entities(devices, True)