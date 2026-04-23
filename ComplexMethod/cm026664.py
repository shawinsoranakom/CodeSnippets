async def _async_update_data(self) -> CometBlueCoordinatorData:
        """Poll the device."""
        data = CometBlueCoordinatorData()

        retry_count = 0

        while retry_count < MAX_RETRIES and not data.temperatures:
            try:
                retry_count += 1
                async with self.device:
                    # temperatures are required and must trigger a retry if not available
                    if not data.temperatures:
                        data.temperatures = await self.device.get_temperature_async()
                    # holiday and battery are optional and should not trigger a retry
                    try:
                        if not data.holiday:
                            data.holiday = await self.device.get_holiday_async(1) or {}
                        if not data.battery:
                            data.battery = await self.device.get_battery_async()
                    except InvalidByteValueError as ex:
                        LOGGER.warning(
                            "Failed to retrieve optional data for %s: %s (%s)",
                            self.name,
                            type(ex).__name__,
                            ex,
                        )
            except (InvalidByteValueError, TimeoutError, BleakError) as ex:
                if retry_count >= MAX_RETRIES:
                    raise UpdateFailed(
                        f"Error retrieving data: {ex}", retry_after=30
                    ) from ex
                LOGGER.info(
                    "Retry updating %s after error: %s (%s)",
                    self.name,
                    type(ex).__name__,
                    ex,
                )
                await asyncio.sleep(COMMAND_RETRY_INTERVAL)
            except Exception as ex:
                raise UpdateFailed(
                    f"({type(ex).__name__}) {ex}", retry_after=30
                ) from ex

        # If one value was not retrieved correctly, keep the old value
        if not data.holiday:
            data.holiday = self.data.holiday
        if not data.battery:
            data.battery = self.data.battery
        LOGGER.debug("Received data for %s: %s", self.name, data)
        return data