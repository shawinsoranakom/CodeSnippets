def get(self, request: web.Request) -> web.Response:
        """Get SpaceAPI data."""
        hass = request.app[KEY_HASS]
        spaceapi: dict[str, Any] = hass.data[DATA_SPACEAPI]

        location = {
            ATTR_LAT: hass.config.latitude,
            ATTR_LON: hass.config.longitude,
        }

        try:
            location[ATTR_ADDRESS] = spaceapi[ATTR_LOCATION][CONF_ADDRESS]
        except KeyError:
            pass
        except TypeError:
            pass

        state_entity_id = spaceapi[CONF_STATE][ATTR_ENTITY_ID]

        state: dict[str, bool | int | float | str | dict[str, str]]
        if (space_state := hass.states.get(state_entity_id)) is not None:
            state = {
                ATTR_OPEN: space_state.state != "off",
                ATTR_LASTCHANGE: dt_util.as_timestamp(space_state.last_updated),
            }
        else:
            state = {
                ATTR_OPEN: "null",
                ATTR_LASTCHANGE: 0,
            }

        with suppress(KeyError):
            state[ATTR_ICON] = {
                ATTR_OPEN: spaceapi[CONF_STATE][CONF_ICON_OPEN],
                ATTR_CLOSED: spaceapi[CONF_STATE][CONF_ICON_CLOSED],
            }

        data = {
            ATTR_API: SPACEAPI_VERSION,
            ATTR_CONTACT: spaceapi[CONF_CONTACT],
            ATTR_ISSUE_REPORT_CHANNELS: spaceapi[CONF_ISSUE_REPORT_CHANNELS],
            ATTR_LOCATION: location,
            ATTR_LOGO: spaceapi[CONF_LOGO],
            ATTR_SPACE: spaceapi[CONF_SPACE],
            ATTR_STATE: state,
            ATTR_URL: spaceapi[CONF_URL],
        }

        with suppress(KeyError):
            data[ATTR_CAM] = spaceapi[CONF_CAM]

        with suppress(KeyError):
            data[ATTR_SPACEFED] = spaceapi[CONF_SPACEFED]

        with suppress(KeyError):
            data[ATTR_STREAM] = spaceapi[CONF_STREAM]

        with suppress(KeyError):
            data[ATTR_FEEDS] = spaceapi[CONF_FEEDS]

        with suppress(KeyError):
            data[ATTR_CACHE] = spaceapi[CONF_CACHE]

        with suppress(KeyError):
            data[ATTR_PROJECTS] = spaceapi[CONF_PROJECTS]

        with suppress(KeyError):
            data[ATTR_RADIO_SHOW] = spaceapi[CONF_RADIO_SHOW]

        sensors: dict[str, list[str]] | None = spaceapi.get(CONF_SENSORS)
        if isinstance(sensors, dict):
            sensors_data: dict[str, list[dict[str, str | float | dict[str, str]]]] = {}
            for sensor_type, entity_ids in sensors.items():
                sensors_data[sensor_type] = [
                    sensor_data
                    for entity_id in entity_ids
                    if (sensor_data := self.get_sensor_data(hass, spaceapi, entity_id))
                    is not None
                ]
            data[ATTR_SENSORS] = sensors_data

        return self.json(data)