async def _async_update_data(self) -> dict:
        """Fetch data from Verisure."""
        try:
            await self.hass.async_add_executor_job(self.verisure.update_cookie)
        except VerisureLoginError:
            LOGGER.debug("Cookie expired, acquiring new cookies")
            try:
                await self.hass.async_add_executor_job(self.verisure.login_cookie)
            except VerisureLoginError as ex:
                LOGGER.error("Credentials expired for Verisure, %s", ex)
                raise ConfigEntryAuthFailed("Credentials expired for Verisure") from ex
            except VerisureError as ex:
                LOGGER.error("Could not log in to verisure, %s", ex)
                raise ConfigEntryAuthFailed("Could not log in to verisure") from ex
        except VerisureError as ex:
            raise UpdateFailed("Unable to update cookie") from ex
        try:
            overview = await self.hass.async_add_executor_job(
                self.verisure.request,
                self.verisure.arm_state(),
                self.verisure.broadband(),
                self.verisure.cameras(),
                self.verisure.climate(),
                self.verisure.door_window(),
                self.verisure.smart_lock(),
                self.verisure.smartplugs(),
            )
        except VerisureError as err:
            LOGGER.error("Could not read overview, %s", err)
            raise UpdateFailed("Could not read overview") from err

        def unpack(overview: list, value: str) -> dict | list:
            unpacked: dict | list | None = next(
                (
                    item["data"]["installation"][value]
                    for item in overview
                    if value in item.get("data", {}).get("installation", {})
                ),
                None,
            )
            return unpacked or []

        # Store data in a way Home Assistant can easily consume it
        self._overview = overview
        return {
            "alarm": unpack(overview, "armState"),
            "broadband": unpack(overview, "broadband"),
            "cameras": {
                device["device"]["deviceLabel"]: device
                for device in unpack(overview, "cameras")
            },
            "climate": {
                device["device"]["deviceLabel"]: device
                for device in unpack(overview, "climates")
            },
            "door_window": {
                device["device"]["deviceLabel"]: device
                for device in unpack(overview, "doorWindows")
            },
            "locks": {
                device["device"]["deviceLabel"]: device
                for device in unpack(overview, "smartLocks")
            },
            "smart_plugs": {
                device["device"]["deviceLabel"]: device
                for device in unpack(overview, "smartplugs")
            },
        }