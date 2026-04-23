async def wait_for_ready(
        self, ready_callback: Callable[[bool], Awaitable[None]]
    ) -> bool:
        """Wait for the client to be ready."""

        if not self.data or Attribute.MAC_ADDRESS not in self.data:
            await self.client.read_mac_address()

            data = await self.client.wait_for_response(
                FunctionalDomain.IDENTIFICATION, 2, WAIT_TIMEOUT
            )

            if not data or Attribute.MAC_ADDRESS not in data:
                _LOGGER.error("Missing MAC address")
                await ready_callback(False)

                return False

        if not self.data or Attribute.THERMOSTAT_MODES not in self.data:
            await self.client.read_thermostat_iaq_available()

            await self.client.wait_for_response(
                FunctionalDomain.CONTROL, 7, WAIT_TIMEOUT
            )

        if (
            not self.data
            or Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS not in self.data
        ):
            await self.client.read_sensors()

            await self.client.wait_for_response(
                FunctionalDomain.SENSORS, 2, WAIT_TIMEOUT
            )

        await self.client.read_thermostat_status()

        await self.client.read_iaq_status()

        await ready_callback(True)

        return True