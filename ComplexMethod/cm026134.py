async def _async_update_data(self):
        if self._devices is None:
            result = await get_list(
                aiohttp_client.async_get_clientsession(self._hass), self._api_key
            )
            if result["state"]:
                self._devices = result["devices"]
            else:
                raise UpdateFailed

        result = await get_states(
            aiohttp_client.async_get_clientsession(self._hass), self._api_key
        )

        for device in self._devices:
            dev = next(
                (dev for dev in result if dev["uid"] == device["uid"]),
                None,
            )
            if dev is not None and "state" in dev:
                device["state"] = dev["state"]
        return self._devices