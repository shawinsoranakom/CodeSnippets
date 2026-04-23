async def update_sensor(self, request: Request, device_id) -> Response:
        """Process a put or post."""
        hass = request.app[KEY_HASS]
        data = hass.data[DOMAIN]

        auth = request.headers.get(AUTHORIZATION)
        tokens = []
        if hass.data[DOMAIN].get(CONF_ACCESS_TOKEN):
            tokens.extend([hass.data[DOMAIN][CONF_ACCESS_TOKEN]])
        tokens.extend(
            [
                entry.data[CONF_ACCESS_TOKEN]
                for entry in hass.config_entries.async_entries(DOMAIN)
                if entry.data.get(CONF_ACCESS_TOKEN)
            ]
        )
        if auth is None or not next(
            (True for token in tokens if hmac.compare_digest(f"Bearer {token}", auth)),
            False,
        ):
            return self.json_message(
                "unauthorized", status_code=HTTPStatus.UNAUTHORIZED
            )

        try:  # Konnected 2.2.0 and above supports JSON payloads
            payload = await request.json()
        except json.decoder.JSONDecodeError:
            _LOGGER.error(
                "Your Konnected device software may be out of "
                "date. Visit https://help.konnected.io for "
                "updating instructions"
            )

        if (device := data[CONF_DEVICES].get(device_id)) is None:
            return self.json_message(
                "unregistered device", status_code=HTTPStatus.BAD_REQUEST
            )

        if (panel := device.get("panel")) is not None:
            # connect if we haven't already
            hass.async_create_task(panel.async_connect())

        try:
            zone_num = str(payload.get(CONF_ZONE) or PIN_TO_ZONE[payload[CONF_PIN]])
            payload[CONF_ZONE] = zone_num
            zone_data = (
                device[CONF_BINARY_SENSORS].get(zone_num)
                or next(
                    (s for s in device[CONF_SWITCHES] if s[CONF_ZONE] == zone_num), None
                )
                or next(
                    (s for s in device[CONF_SENSORS] if s[CONF_ZONE] == zone_num), None
                )
            )
        except KeyError:
            zone_data = None

        if zone_data is None:
            return self.json_message(
                "unregistered sensor/actuator", status_code=HTTPStatus.BAD_REQUEST
            )

        zone_data["device_id"] = device_id

        for attr in ("state", "temp", "humi", "addr"):
            value = payload.get(attr)
            handler = HANDLERS.get(attr)
            if value is not None and handler:
                hass.async_create_task(handler(hass, zone_data, payload))

        return self.json_message("ok")