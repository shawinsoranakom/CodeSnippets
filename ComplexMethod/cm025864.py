async def _run_update(self, force_refresh_token: bool) -> Lyric:
        """Fetch data from Lyric."""
        try:
            if not force_refresh_token:
                await self.oauth_session.async_ensure_token_valid()
            else:
                await self.oauth_session.force_refresh_token()
        except ClientResponseError as exception:
            if exception.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                raise ConfigEntryAuthFailed from exception
            raise UpdateFailed(exception) from exception

        try:
            async with asyncio.timeout(60):
                await self.lyric.get_locations()
                await asyncio.gather(
                    *(
                        self.lyric.get_thermostat_rooms(
                            location.location_id, device.device_id
                        )
                        for location in self.lyric.locations
                        for device in location.devices
                        if device.device_class == "Thermostat"
                        and device.device_id.startswith("LCC")
                    )
                )

        except LyricAuthenticationException as exception:
            # Attempt to refresh the token before failing.
            # Honeywell appear to have issues keeping tokens saved.
            _LOGGER.debug("Authentication failed. Attempting to refresh token")
            if not force_refresh_token:
                return await self._run_update(True)
            raise ConfigEntryAuthFailed from exception
        except (LyricException, ClientResponseError) as exception:
            raise UpdateFailed(exception) from exception
        return self.lyric