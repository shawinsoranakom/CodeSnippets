async def put(  # noqa: C901
        self, request: web.Request, username: str, entity_number: str
    ) -> web.Response:
        """Process a request to set the state of an individual light."""
        assert request.remote is not None
        if not _remote_is_allowed(request.remote):
            return self.json_message("Only local IPs allowed", HTTPStatus.UNAUTHORIZED)

        config = self.config
        hass = request.app[KEY_HASS]
        entity_id = config.number_to_entity_id(entity_number)

        if entity_id is None:
            _LOGGER.error("Unknown entity number: %s", entity_number)
            return self.json_message("Entity not found", HTTPStatus.NOT_FOUND)

        if (entity := hass.states.get(entity_id)) is None:
            _LOGGER.error("Entity not found: %s", entity_id)
            return self.json_message("Entity not found", HTTPStatus.NOT_FOUND)

        if not config.is_state_exposed(entity):
            _LOGGER.error("Entity not exposed: %s", entity_id)
            return self.json_message("Entity not exposed", HTTPStatus.UNAUTHORIZED)

        try:
            request_json = await request.json()
        except ValueError:
            _LOGGER.error("Received invalid json")
            return self.json_message("Invalid JSON", HTTPStatus.BAD_REQUEST)

        # Get the entity's supported features
        entity_features = entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        if entity.domain == light.DOMAIN:
            color_modes = entity.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) or []

        # Parse the request
        parsed: dict[str, Any] = {
            STATE_ON: False,
            STATE_BRIGHTNESS: None,
            STATE_HUE: None,
            STATE_SATURATION: None,
            STATE_COLOR_TEMP: None,
            STATE_XY: None,
            STATE_TRANSITION: None,
        }

        if HUE_API_STATE_ON in request_json:
            if not isinstance(request_json[HUE_API_STATE_ON], bool):
                _LOGGER.error("Unable to parse data: %s", request_json)
                return self.json_message("Bad request", HTTPStatus.BAD_REQUEST)
            parsed[STATE_ON] = request_json[HUE_API_STATE_ON]
        else:
            parsed[STATE_ON] = _hass_to_hue_state(entity)

        for key, attr in (
            (HUE_API_STATE_BRI, STATE_BRIGHTNESS),
            (HUE_API_STATE_HUE, STATE_HUE),
            (HUE_API_STATE_SAT, STATE_SATURATION),
            (HUE_API_STATE_CT, STATE_COLOR_TEMP),
            (HUE_API_STATE_TRANSITION, STATE_TRANSITION),
        ):
            if key in request_json:
                try:
                    parsed[attr] = int(request_json[key])
                except ValueError:
                    _LOGGER.error("Unable to parse data (2): %s", request_json)
                    return self.json_message("Bad request", HTTPStatus.BAD_REQUEST)
        if HUE_API_STATE_XY in request_json:
            try:
                parsed[STATE_XY] = (
                    float(request_json[HUE_API_STATE_XY][0]),
                    float(request_json[HUE_API_STATE_XY][1]),
                )
            except ValueError:
                _LOGGER.error("Unable to parse data (2): %s", request_json)
                return self.json_message("Bad request", HTTPStatus.BAD_REQUEST)

        if HUE_API_STATE_BRI in request_json:
            if entity.domain == light.DOMAIN:
                if light.brightness_supported(color_modes):
                    parsed[STATE_ON] = parsed[STATE_BRIGHTNESS] > 0
                else:
                    parsed[STATE_BRIGHTNESS] = None

            elif entity.domain == scene.DOMAIN:
                parsed[STATE_BRIGHTNESS] = None
                parsed[STATE_ON] = True

            elif entity.domain in [
                script.DOMAIN,
                media_player.DOMAIN,
                fan.DOMAIN,
                cover.DOMAIN,
                climate.DOMAIN,
                humidifier.DOMAIN,
            ]:
                # Convert 0-254 to 0-100
                level = (parsed[STATE_BRIGHTNESS] / HUE_API_STATE_BRI_MAX) * 100
                parsed[STATE_BRIGHTNESS] = round(level)
                parsed[STATE_ON] = True

        # Choose general HA domain
        domain = core.DOMAIN

        # Entity needs separate call to turn on
        turn_on_needed = False

        # Convert the resulting "on" status into the service we need to call
        service: str | None = SERVICE_TURN_ON if parsed[STATE_ON] else SERVICE_TURN_OFF

        # Construct what we need to send to the service
        data: dict[str, Any] = {ATTR_ENTITY_ID: entity_id}

        # If the requested entity is a light, set the brightness, hue,
        # saturation and color temp
        if entity.domain == light.DOMAIN:
            if parsed[STATE_ON]:
                if (
                    light.brightness_supported(color_modes)
                    and parsed[STATE_BRIGHTNESS] is not None
                ):
                    data[ATTR_BRIGHTNESS] = hue_brightness_to_hass(
                        parsed[STATE_BRIGHTNESS]
                    )

                if light.color_supported(color_modes):
                    if any((parsed[STATE_HUE], parsed[STATE_SATURATION])):
                        if parsed[STATE_HUE] is not None:
                            hue = parsed[STATE_HUE]
                        else:
                            hue = 0

                        if parsed[STATE_SATURATION] is not None:
                            sat = parsed[STATE_SATURATION]
                        else:
                            sat = 0

                        # Convert hs values to hass hs values
                        hue = int((hue / HUE_API_STATE_HUE_MAX) * 360)
                        sat = int((sat / HUE_API_STATE_SAT_MAX) * 100)

                        data[ATTR_HS_COLOR] = (hue, sat)

                    if parsed[STATE_XY] is not None:
                        data[ATTR_XY_COLOR] = parsed[STATE_XY]

                if (
                    light.color_temp_supported(color_modes)
                    and parsed[STATE_COLOR_TEMP] is not None
                ):
                    data[ATTR_COLOR_TEMP_KELVIN] = (
                        color_util.color_temperature_mired_to_kelvin(
                            parsed[STATE_COLOR_TEMP]
                        )
                    )

                if (
                    entity_features & LightEntityFeature.TRANSITION
                    and parsed[STATE_TRANSITION] is not None
                ):
                    data[ATTR_TRANSITION] = parsed[STATE_TRANSITION] / 10

        # If the requested entity is a script, add some variables
        elif entity.domain == script.DOMAIN:
            data["variables"] = {
                "requested_state": STATE_ON if parsed[STATE_ON] else STATE_OFF
            }

            if parsed[STATE_BRIGHTNESS] is not None:
                data["variables"]["requested_level"] = parsed[STATE_BRIGHTNESS]

        # If the requested entity is a climate, set the temperature
        elif entity.domain == climate.DOMAIN:
            # We don't support turning climate devices on or off,
            # only setting the temperature
            service = None

            if (
                entity_features & ClimateEntityFeature.TARGET_TEMPERATURE
                and parsed[STATE_BRIGHTNESS] is not None
            ):
                domain = entity.domain
                service = SERVICE_SET_TEMPERATURE
                data[ATTR_TEMPERATURE] = parsed[STATE_BRIGHTNESS]

        # If the requested entity is a humidifier, set the humidity
        elif entity.domain == humidifier.DOMAIN:
            if parsed[STATE_BRIGHTNESS] is not None:
                turn_on_needed = True
                domain = entity.domain
                service = SERVICE_SET_HUMIDITY
                data[ATTR_HUMIDITY] = parsed[STATE_BRIGHTNESS]

        # If the requested entity is a media player, convert to volume
        elif entity.domain == media_player.DOMAIN:
            if (
                entity_features & MediaPlayerEntityFeature.VOLUME_SET
                and parsed[STATE_BRIGHTNESS] is not None
            ):
                turn_on_needed = True
                domain = entity.domain
                service = SERVICE_VOLUME_SET
                # Convert 0-100 to 0.0-1.0
                data[ATTR_MEDIA_VOLUME_LEVEL] = parsed[STATE_BRIGHTNESS] / 100.0

        # If the requested entity is a cover, convert to open_cover/close_cover
        elif entity.domain == cover.DOMAIN:
            domain = entity.domain
            if service == SERVICE_TURN_ON:
                service = SERVICE_OPEN_COVER
            else:
                service = SERVICE_CLOSE_COVER

            if (
                entity_features & CoverEntityFeature.SET_POSITION
                and parsed[STATE_BRIGHTNESS] is not None
            ):
                domain = entity.domain
                service = SERVICE_SET_COVER_POSITION
                data[ATTR_POSITION] = parsed[STATE_BRIGHTNESS]

        # If the requested entity is a fan, convert to speed
        elif (
            entity.domain == fan.DOMAIN
            and entity_features & FanEntityFeature.SET_SPEED
            and parsed[STATE_BRIGHTNESS] is not None
        ):
            domain = entity.domain
            # Convert 0-100 to a fan speed
            data[ATTR_PERCENTAGE] = parsed[STATE_BRIGHTNESS]

        # Map the off command to on
        if entity.domain in config.off_maps_to_on_domains:
            service = SERVICE_TURN_ON

        # Separate call to turn on needed
        if turn_on_needed:
            await hass.services.async_call(
                core.DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: entity_id},
                blocking=False,
            )

        if service is not None:
            state_will_change = parsed[STATE_ON] != _hass_to_hue_state(entity)

            await hass.services.async_call(domain, service, data, blocking=False)

            if state_will_change:
                # Wait for the state to change.
                await wait_for_state_change_or_timeout(
                    hass, entity_id, STATE_CACHED_TIMEOUT
                )

        # Create success responses for all received keys
        json_response = [
            create_hue_success_response(
                entity_number, HUE_API_STATE_ON, parsed[STATE_ON]
            )
        ]

        for key, val in (
            (STATE_BRIGHTNESS, HUE_API_STATE_BRI),
            (STATE_HUE, HUE_API_STATE_HUE),
            (STATE_SATURATION, HUE_API_STATE_SAT),
            (STATE_COLOR_TEMP, HUE_API_STATE_CT),
            (STATE_XY, HUE_API_STATE_XY),
            (STATE_TRANSITION, HUE_API_STATE_TRANSITION),
        ):
            if parsed[key] is not None:
                json_response.append(
                    create_hue_success_response(entity_number, val, parsed[key])
                )

        if entity.domain in config.off_maps_to_on_domains:
            # Caching is required because things like scripts and scenes won't
            # report as "off" to Alexa if an "off" command is received, because
            # they'll map to "on". Thus, instead of reporting its actual
            # status, we report what Alexa will want to see, which is the same
            # as the actual requested command.
            config.cached_states[entity_id] = [parsed, None]
        else:
            config.cached_states[entity_id] = [parsed, time.time()]

        return self.json(json_response)