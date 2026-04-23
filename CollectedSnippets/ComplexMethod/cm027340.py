async def async_update(self) -> None:
        """Get the data from Kaiterra API."""

        try:
            async with asyncio.timeout(10):
                data = await self._api.get_latest_sensor_readings(self._devices)
        except (ClientResponseError, ClientConnectorError, TimeoutError) as err:
            _LOGGER.debug("Couldn't fetch data from Kaiterra API: %s", err)
            self.data = {}
            async_dispatcher_send(self._hass, DISPATCHER_KAITERRA)
            return

        _LOGGER.debug("New data retrieved: %s", data)

        try:
            self.data = {}
            for i, device in enumerate(data):
                if not device:
                    self.data[self._devices_ids[i]] = {}
                    continue

                aqi, main_pollutant = None, None
                for sensor_name, sensor in device.items():
                    if not (points := sensor.get("points")):
                        continue

                    point = points[0]
                    sensor["value"] = point.get("value")

                    if "aqi" not in point:
                        continue

                    sensor["aqi"] = point["aqi"]
                    if not aqi or aqi < point["aqi"]:
                        aqi = point["aqi"]
                        main_pollutant = POLLUTANTS.get(sensor_name)

                level = None
                if aqi is not None:
                    for j in range(1, len(self._scale)):
                        if aqi <= self._scale[j]:
                            level = self._level[j - 1]
                            break

                device["aqi"] = {"value": aqi}
                device["aqi_level"] = {"value": level}
                device["aqi_pollutant"] = {"value": main_pollutant}

                self.data[self._devices_ids[i]] = device
        except IndexError as err:
            _LOGGER.error("Parsing error %s", err)
        except TypeError as err:
            _LOGGER.error("Type error %s", err)

        async_dispatcher_send(self._hass, DISPATCHER_KAITERRA)