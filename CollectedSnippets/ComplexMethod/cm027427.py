async def _async_update_data(self) -> T:
        """Fetch the latest data from the source."""

        if self._hub.is_throttled():
            if not self._has_already_worked:
                raise UpdateFailed("Renault hub currently throttled: init skipped")
            # we have been throttled and decided to cooldown
            # so do not count this update as an error
            # coordinator. last_update_success should still be ok
            self.logger.debug("Renault hub currently throttled: scan skipped")
            self.assumed_state = True
            return self.data

        try:
            async with _PARALLEL_SEMAPHORE:
                data = await self.update_method()

        except AccessDeniedException as err:
            # This can mean both a temporary error or a permanent error. If it has
            # worked before, make it temporary, if not disable the update interval.
            if not self._has_already_worked:
                self.update_interval = None
                self.access_denied = True
            raise UpdateFailed(f"This endpoint is denied: {err}") from err

        except QuotaLimitException as err:
            # The data we got is not bad per see, initiate cooldown for all coordinators
            self._hub.set_throttled()
            if self._has_already_worked:
                self.assumed_state = True
                self.logger.warning("Renault API throttled")
                return self.data

            raise UpdateFailed(f"Renault API throttled: {err}") from err

        except NotSupportedException as err:
            # Disable because the vehicle does not support this Renault endpoint.
            self.update_interval = None
            self.not_supported = True
            raise UpdateFailed(f"This endpoint is not supported: {err}") from err

        except KamereonResponseException as err:
            # Other Renault errors.
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        self._has_already_worked = True
        self.assumed_state = False
        return data