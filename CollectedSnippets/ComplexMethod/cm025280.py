def _setup(self, hass: HomeAssistant) -> None:
        """Rachio device setup."""
        rachio = self.rachio

        response = rachio.person.info()
        if is_invalid_auth_code(int(response[0][KEY_STATUS])):
            raise ConfigEntryAuthFailed(f"API key error: {response}")
        if int(response[0][KEY_STATUS]) != HTTPStatus.OK:
            raise ConfigEntryNotReady(f"API Error: {response}")
        self._id = response[1][KEY_ID]

        # Use user ID to get user data
        data = rachio.person.get(self._id)
        if is_invalid_auth_code(int(data[0][KEY_STATUS])):
            raise ConfigEntryAuthFailed(f"User ID error: {data}")
        if int(data[0][KEY_STATUS]) != HTTPStatus.OK:
            raise ConfigEntryNotReady(f"API Error: {data}")
        self.username = data[1][KEY_USERNAME]
        devices: list[dict[str, Any]] = data[1][KEY_DEVICES]
        base_station_data = rachio.valve.list_base_stations(self._id)
        base_stations: list[dict[str, Any]] = base_station_data[1][KEY_BASE_STATIONS]

        for controller in devices:
            webhooks = rachio.notification.get_device_webhook(controller[KEY_ID])[1]
            # The API does not provide a way to tell if a controller is shared
            # or if they are the owner. To work around this problem we fetch the webhooks
            # before we setup the device so we can skip it instead of failing.
            # webhooks are normally a list, however if there is an error
            # rachio hands us back a dict
            if isinstance(webhooks, dict):
                if webhooks.get("code") == PERMISSION_ERROR:
                    _LOGGER.warning(
                        (
                            "Not adding controller '%s', only controllers owned by '%s'"
                            " may be added"
                        ),
                        controller[KEY_NAME],
                        self.username,
                    )
                else:
                    _LOGGER.error(
                        "Failed to add rachio controller '%s' because of an error: %s",
                        controller[KEY_NAME],
                        webhooks.get("error", "Unknown Error"),
                    )
                continue

            rachio_iro = RachioIro(hass, rachio, controller, webhooks)
            rachio_iro.setup()
            self._controllers.append(rachio_iro)

        base_count = len(base_stations)
        self._base_stations.extend(
            RachioBaseStation(
                rachio,
                base,
                RachioUpdateCoordinator(
                    hass, rachio, self.config_entry, base, base_count
                ),
                RachioScheduleUpdateCoordinator(hass, rachio, self.config_entry, base),
            )
            for base in base_stations
        )

        _LOGGER.debug('Using Rachio API as user "%s"', self.username)