async def get(self, request: Request, device_id) -> Response:
        """Return the current binary state of a switch."""
        hass = request.app[KEY_HASS]
        data = hass.data[DOMAIN]

        if not (device := data[CONF_DEVICES].get(device_id)):
            return self.json_message(
                f"Device {device_id} not configured", status_code=HTTPStatus.NOT_FOUND
            )

        if (panel := device.get("panel")) is not None:
            # connect if we haven't already
            hass.async_create_task(panel.async_connect())

        # Our data model is based on zone ids but we convert from/to pin ids
        # based on whether they are specified in the request
        try:
            zone_num = str(
                request.query.get(CONF_ZONE) or PIN_TO_ZONE[request.query[CONF_PIN]]
            )
            zone = next(
                switch
                for switch in device[CONF_SWITCHES]
                if switch[CONF_ZONE] == zone_num
            )

        except StopIteration:
            zone = None
        except KeyError:
            zone = None
            zone_num = None

        if not zone:
            target = request.query.get(
                CONF_ZONE, request.query.get(CONF_PIN, "unknown")
            )
            return self.json_message(
                f"Switch on zone or pin {target} not configured",
                status_code=HTTPStatus.NOT_FOUND,
            )

        resp = {}
        if request.query.get(CONF_ZONE):
            resp[CONF_ZONE] = zone_num
        elif zone_num:
            resp[CONF_PIN] = ZONE_TO_PIN[zone_num]

        # Make sure entity is setup
        if zone_entity_id := zone.get(ATTR_ENTITY_ID):
            resp["state"] = self.binary_value(
                hass.states.get(zone_entity_id).state,  # type: ignore[union-attr]
                zone[CONF_ACTIVATION],
            )
            return self.json(resp)

        _LOGGER.warning("Konnected entity not yet setup, returning default")
        resp["state"] = self.binary_value(STATE_OFF, zone[CONF_ACTIVATION])
        return self.json(resp)