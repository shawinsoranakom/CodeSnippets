async def initialize(self) -> None:
        """Init controller."""
        try:
            devices = await self._api_client.get_devices()
            credentials = await self._authenticator.authenticate()

            if devices.mqtt:
                mqtt = await self._get_mqtt_client()
                mqtt_devices = [
                    Device(info, self._authenticator) for info in devices.mqtt
                ]
                async with asyncio.TaskGroup() as tg:

                    async def _init(device: Device) -> None:
                        """Initialize MQTT device."""
                        await device.initialize(mqtt)
                        self._devices.append(device)

                    for device in mqtt_devices:
                        tg.create_task(_init(device))

            for device_config in devices.xmpp:
                bot = VacBot(
                    credentials.user_id,
                    EcoVacsAPI.REALM,
                    self._device_id[0:8],
                    credentials.token,
                    device_config,
                    self._continent,
                    monitor=True,
                )
                self._legacy_devices.append(bot)
            for device_config in devices.not_supported:
                _LOGGER.warning(
                    (
                        'Device "%s" not supported. More information at '
                        "https://github.com/DeebotUniverse/client.py/issues/612: %s"
                    ),
                    device_config["deviceName"],
                    device_config,
                )

        except InvalidAuthenticationError as ex:
            raise ConfigEntryError("Invalid credentials") from ex
        except DeebotError as ex:
            raise ConfigEntryNotReady("Error during setup") from ex

        _LOGGER.debug("Controller initialize complete")