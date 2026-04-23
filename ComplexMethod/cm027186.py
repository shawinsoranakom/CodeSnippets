def __init__(self, hass: HomeAssistant, conf: ConfigType, local_ip: str) -> None:
        """Initialize the instance."""
        self.hass = hass
        self.type = conf.get(CONF_TYPE)
        self.numbers: dict[str, str] = {}
        self.store: storage.Store | None = None
        self.cached_states: dict[str, list] = {}
        self._exposed_cache: dict[str, bool] = {}

        if self.type == TYPE_ALEXA:
            _LOGGER.warning(
                "Emulated Hue running in legacy mode because type has been "
                "specified. More info at https://goo.gl/M6tgz8"
            )

        # Get the IP address that will be passed to the Echo during discovery
        self.host_ip_addr: str = conf.get(CONF_HOST_IP) or local_ip

        # Get the port that the Hue bridge will listen on
        self.listen_port: int = conf.get(CONF_LISTEN_PORT) or DEFAULT_LISTEN_PORT

        # Get whether or not UPNP binds to multicast address (239.255.255.250)
        # or to the unicast address (host_ip_addr)
        self.upnp_bind_multicast: bool = conf.get(
            CONF_UPNP_BIND_MULTICAST, DEFAULT_UPNP_BIND_MULTICAST
        )

        # Get domains that cause both "on" and "off" commands to map to "on"
        # This is primarily useful for things like scenes or scripts, which
        # don't really have a concept of being off
        off_maps_to_on_domains = conf.get(CONF_OFF_MAPS_TO_ON_DOMAINS)
        if isinstance(off_maps_to_on_domains, list):
            self.off_maps_to_on_domains = set(off_maps_to_on_domains)
        else:
            self.off_maps_to_on_domains = DEFAULT_OFF_MAPS_TO_ON_DOMAINS

        # Get whether or not entities should be exposed by default, or if only
        # explicitly marked ones will be exposed
        self.expose_by_default: bool = conf.get(
            CONF_EXPOSE_BY_DEFAULT, DEFAULT_EXPOSE_BY_DEFAULT
        )

        # Get domains that are exposed by default when expose_by_default is
        # True
        self.exposed_domains = set(
            conf.get(CONF_EXPOSED_DOMAINS, DEFAULT_EXPOSED_DOMAINS)
        )

        # Calculated effective advertised IP and port for network isolation
        self.advertise_ip: str = conf.get(CONF_ADVERTISE_IP) or self.host_ip_addr

        self.advertise_port: int = conf.get(CONF_ADVERTISE_PORT) or self.listen_port

        self.entities: dict[str, dict[str, str]] = conf.get(CONF_ENTITIES, {})

        self._entities_with_hidden_attr_in_config = {}
        for entity_id in self.entities:
            hidden_value = self.entities[entity_id].get(CONF_ENTITY_HIDDEN)
            if hidden_value is not None:
                self._entities_with_hidden_attr_in_config[entity_id] = hidden_value

        # Get whether all non-dimmable lights should be reported as dimmable
        # for compatibility with older installations.
        self.lights_all_dimmable: bool = conf.get(CONF_LIGHTS_ALL_DIMMABLE) or False

        if self.expose_by_default:
            self.track_domains = set(self.exposed_domains) or SUPPORTED_DOMAINS
        else:
            self.track_domains = {
                split_entity_id(entity_id)[0] for entity_id in self.entities
            }