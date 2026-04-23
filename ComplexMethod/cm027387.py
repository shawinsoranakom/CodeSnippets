async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the SNMP sensor."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    community = config.get(CONF_COMMUNITY)
    baseoid: str = config[CONF_BASEOID]
    version = config[CONF_VERSION]
    username = config.get(CONF_USERNAME)
    authkey = config.get(CONF_AUTH_KEY)
    authproto = config[CONF_AUTH_PROTOCOL]
    privkey = config.get(CONF_PRIV_KEY)
    privproto = config[CONF_PRIV_PROTOCOL]
    accept_errors = config.get(CONF_ACCEPT_ERRORS)
    default_value = config.get(CONF_DEFAULT_VALUE)

    try:
        # Try IPv4 first.
        target = await UdpTransportTarget.create((host, port), timeout=DEFAULT_TIMEOUT)
    except PySnmpError:
        # Then try IPv6.
        try:
            target = Udp6TransportTarget((host, port), timeout=DEFAULT_TIMEOUT)
        except PySnmpError as err:
            _LOGGER.error("Invalid SNMP host: %s", err)
            return

    if version == "3":
        if not authkey:
            authproto = "none"
        if not privkey:
            privproto = "none"
        auth_data = UsmUserData(
            username,
            authKey=authkey or None,
            privKey=privkey or None,
            authProtocol=getattr(hlapi, MAP_AUTH_PROTOCOLS[authproto]),
            privProtocol=getattr(hlapi, MAP_PRIV_PROTOCOLS[privproto]),
        )
    else:
        auth_data = CommunityData(community, mpModel=SNMP_VERSIONS[version])

    request_args = await async_create_request_cmd_args(hass, auth_data, target, baseoid)
    get_result = await get_cmd(*request_args)
    errindication, _, _, _ = get_result

    if errindication and not accept_errors:
        _LOGGER.error(
            "Please check the details in the configuration file: %s",
            errindication,
        )
        return

    name = config.get(CONF_NAME, Template(DEFAULT_NAME, hass))
    trigger_entity_config = {CONF_NAME: name}
    for key in TRIGGER_ENTITY_OPTIONS:
        if key not in config:
            continue
        trigger_entity_config[key] = config[key]

    value_template: ValueTemplate | None = config.get(CONF_VALUE_TEMPLATE)

    data = SnmpData(request_args, baseoid, accept_errors, default_value)
    async_add_entities([SnmpSensor(hass, data, trigger_entity_config, value_template)])