async def _async_try_connect(self) -> dict[str, str]:
        """Try to connect to the Pi-hole API and determine the version."""
        try:
            version = await determine_api_version(hass=self.hass, entry=self._config)
        except HoleError:
            return {"base": "cannot_connect"}
        pi_hole: Hole = api_by_version(self.hass, self._config, version)

        if version == 6:
            try:
                await pi_hole.authenticate()
                _LOGGER.debug("Success authenticating with pihole API version: %s", 6)
            except HoleError:
                _LOGGER.debug("Failed authenticating with pihole API version: %s", 6)
                return {CONF_API_KEY: "invalid_auth"}

        elif version == 5:
            try:
                await pi_hole.get_data()
                if pi_hole.data is not None and "error" in pi_hole.data:
                    _LOGGER.debug(
                        "API version %s returned an unexpected error: %s",
                        5,
                        str(pi_hole.data),
                    )
                    raise HoleError(pi_hole.data)  # noqa: TRY301
            except HoleError as ex_v5:
                _LOGGER.error(
                    "Connection to API version 5 failed: %s",
                    ex_v5,
                )
                return {"base": "cannot_connect"}
            else:
                _LOGGER.debug(
                    "Success connecting to, but necessarily authenticating with, pihole, API version is: %s",
                    5,
                )
            # the v5 API returns an empty list to unauthenticated requests.
            if not isinstance(pi_hole.data, dict):
                _LOGGER.debug(
                    "API version %s returned %s, '[]' is expected for unauthenticated requests",
                    5,
                    pi_hole.data,
                )
                return {CONF_API_KEY: "invalid_auth"}
        return {}