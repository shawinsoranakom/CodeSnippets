def __init__(
        self,
        hass: HomeAssistant,
        driver: HomeDriver,
        name: str,
        entity_id: str,
        aid: int,
        config: dict[str, Any],
        *args: Any,
        category: int = CATEGORY_OTHER,
        device_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a Accessory object."""
        super().__init__(
            driver=driver,
            display_name=cleanup_name_for_homekit(name),
            aid=aid,
            iid_manager=HomeIIDManager(driver.iid_storage),
            *args,  # noqa: B026
            **kwargs,
        )
        self._reload_on_change_attrs = list(RELOAD_ON_CHANGE_ATTRS)
        self.config = config or {}
        if device_id:
            self.device_id: str | None = device_id
            serial_number = device_id
            domain = None
        else:
            self.device_id = None
            serial_number = entity_id
            domain = split_entity_id(entity_id)[0].replace("_", " ")

        if self.config.get(ATTR_MANUFACTURER) is not None:
            manufacturer = str(self.config[ATTR_MANUFACTURER])
        elif self.config.get(ATTR_INTEGRATION) is not None:
            manufacturer = self.config[ATTR_INTEGRATION].replace("_", " ").title()
        elif domain:
            manufacturer = f"{MANUFACTURER} {domain}".title()
        else:
            manufacturer = MANUFACTURER
        if self.config.get(ATTR_MODEL) is not None:
            model = str(self.config[ATTR_MODEL])
        elif domain:
            model = domain.title()
        else:
            model = MANUFACTURER
        sw_version = None
        if self.config.get(ATTR_SW_VERSION) is not None:
            sw_version = format_version(self.config[ATTR_SW_VERSION])
        if sw_version is None:
            sw_version = format_version(__version__)
            assert sw_version is not None
        hw_version = None
        if self.config.get(ATTR_HW_VERSION) is not None:
            hw_version = format_version(self.config[ATTR_HW_VERSION])

        self.set_info_service(
            manufacturer=manufacturer[:MAX_MANUFACTURER_LENGTH],
            model=model[:MAX_MODEL_LENGTH],
            serial_number=serial_number[:MAX_SERIAL_LENGTH],
            firmware_revision=sw_version[:MAX_VERSION_LENGTH],
        )
        if hw_version:
            serv_info = self.get_service(SERV_ACCESSORY_INFO)
            char = self.driver.loader.get_char(CHAR_HARDWARE_REVISION)
            serv_info.add_characteristic(char)
            serv_info.configure_char(
                CHAR_HARDWARE_REVISION, value=hw_version[:MAX_VERSION_LENGTH]
            )
            char.broker = self
            self.iid_manager.assign(char)

        self.category = category
        self.entity_id = entity_id
        self.hass = hass
        self._subscriptions: list[CALLBACK_TYPE] = []

        if device_id:
            return

        self._char_battery = None
        self._char_charging = None
        self._char_low_battery = None
        self.linked_battery_sensor = self.config.get(CONF_LINKED_BATTERY_SENSOR)
        self.linked_battery_charging_sensor = self.config.get(
            CONF_LINKED_BATTERY_CHARGING_SENSOR
        )
        self.low_battery_threshold = self.config.get(
            CONF_LOW_BATTERY_THRESHOLD, DEFAULT_LOW_BATTERY_THRESHOLD
        )

        """Add battery service if available"""
        state = self.hass.states.get(self.entity_id)
        self._update_available_from_state(state)
        assert state is not None
        entity_attributes = state.attributes
        battery_found = entity_attributes.get(ATTR_BATTERY_LEVEL)

        if self.linked_battery_sensor:
            state = self.hass.states.get(self.linked_battery_sensor)
            if state is not None:
                battery_found = state.state
            else:
                _LOGGER.warning(
                    "%s: Battery sensor state missing: %s",
                    self.entity_id,
                    self.linked_battery_sensor,
                )
                self.linked_battery_sensor = None

        if not battery_found:
            return

        _LOGGER.debug("%s: Found battery level", self.entity_id)

        if self.linked_battery_charging_sensor:
            state = self.hass.states.get(self.linked_battery_charging_sensor)
            if state is None:
                self.linked_battery_charging_sensor = None
                _LOGGER.warning(
                    "%s: Battery charging binary_sensor state missing: %s",
                    self.entity_id,
                    self.linked_battery_charging_sensor,
                )
            else:
                _LOGGER.debug("%s: Found battery charging", self.entity_id)

        serv_battery = self.add_preload_service(SERV_BATTERY_SERVICE)
        self._char_battery = serv_battery.configure_char(CHAR_BATTERY_LEVEL, value=0)
        self._char_charging = serv_battery.configure_char(
            CHAR_CHARGING_STATE, value=HK_NOT_CHARGABLE
        )
        self._char_low_battery = serv_battery.configure_char(
            CHAR_STATUS_LOW_BATTERY, value=0
        )