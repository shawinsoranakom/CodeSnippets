async def _async_update_data(self) -> dict[str, Any]:
        """Update the state of the device."""
        _LOGGER.debug(
            "Updating device state: %s, error count: %d", self.name, self._error_count
        )
        try:
            await self.device.update_state()
        except DeviceNotBoundError as error:
            raise UpdateFailed(
                f"Device {self.name} is unavailable, device is not bound."
            ) from error
        except DeviceTimeoutError as error:
            self._error_count += 1

            # Under normal conditions GREE units timeout every once in a while
            if self.last_update_success and self._error_count >= MAX_ERRORS:
                _LOGGER.warning(
                    "Device %s is unavailable: %s", self.name, self.device.device_info
                )
                raise UpdateFailed(
                    f"Device {self.name} is unavailable, could not send update request"
                ) from error
        else:
            # raise update failed if time for more than MAX_ERRORS has passed since last update
            now = utcnow()
            elapsed_success = now - self._last_response_time
            if self.update_interval and elapsed_success >= timedelta(
                seconds=MAX_EXPECTED_RESPONSE_TIME_INTERVAL
            ):
                if not self._last_error_time or (
                    (now - self.update_interval) >= self._last_error_time
                ):
                    self._last_error_time = now
                    self._error_count += 1

                _LOGGER.warning(
                    "Device %s took an unusually long time to respond, %s seconds",
                    self.name,
                    elapsed_success,
                )
            else:
                self._error_count = 0
            if self.last_update_success and self._error_count >= MAX_ERRORS:
                raise UpdateFailed(
                    f"Device {self.name} is unresponsive for too long and now unavailable"
                )

        self._last_response_time = utcnow()
        return copy.deepcopy(self.device.raw_properties)