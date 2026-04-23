async def _async_poll(self) -> None:
        """Poll the device to retrieve any extra data."""
        assert self._last_service_info

        try:
            update = await self._async_poll_data(self._last_service_info)
        except BleakError as exc:
            if self.last_poll_successful:
                self.logger.error(
                    "%s: Bluetooth error whilst polling: %s", self.address, str(exc)
                )
                self.last_poll_successful = False
            return
        except Exception:
            if self.last_poll_successful:
                self.logger.exception("%s: Failure while polling", self.address)
                self.last_poll_successful = False
            return
        finally:
            self._last_poll = monotonic_time_coarse()

        if not self.last_poll_successful:
            self.logger.debug("%s: Polling recovered", self.address)
            self.last_poll_successful = True

        for processor in self._processors:
            processor.async_handle_update(update)