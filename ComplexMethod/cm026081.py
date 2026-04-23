async def _update_data(self) -> PowerwallData:
        """Fetch data from API endpoint."""
        _LOGGER.debug("Updating data")
        for attempt in range(2):
            try:
                if attempt == 1:
                    await self._recreate_powerwall_login()
                data = await _fetch_powerwall_data(self.power_wall)
            except (TimeoutError, PowerwallUnreachableError) as err:
                raise UpdateFailed("Unable to fetch data from powerwall") from err
            except MissingAttributeError as err:
                _LOGGER.error("The powerwall api has changed: %s", str(err))
                # The error might include some important information
                # about what exactly changed.
                persistent_notification.create(
                    self.hass, API_CHANGED_ERROR_BODY, API_CHANGED_TITLE
                )
                self.runtime_data[POWERWALL_API_CHANGED] = True
                raise UpdateFailed("The powerwall api has changed") from err
            except AccessDeniedError as err:
                if attempt == 1:
                    # failed to authenticate => the credentials must be wrong
                    raise ConfigEntryAuthFailed from err
                if self.password is None:
                    raise ConfigEntryAuthFailed from err
                _LOGGER.debug("Access denied, trying to reauthenticate")
                # there is still an attempt left to authenticate,
                # so we continue in the loop
            except ApiError as err:
                raise UpdateFailed(f"Updated failed due to {err}, will retry") from err
            else:
                return data
        raise RuntimeError("unreachable")