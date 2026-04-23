async def _async_setup(self) -> None:
        """Set up the coordinator."""
        async with asyncio.timeout(10):
            expiry_time = (
                self.refresh_token_creation_time
                + REFRESH_TOKEN_EXPIRY_TIME.total_seconds()
            )
            try:
                if datetime.now().timestamp() >= expiry_time:
                    await self.update_refresh_token()
                else:
                    await self.api.authenticate_refresh(
                        self.refresh_token, async_get_clientsession(self.hass)
                    )
                _LOGGER.debug("Authenticated with Nice G.O. API")

                barriers = await self.api.get_all_barriers()
                parsed_barriers = [
                    await self._parse_barrier(barrier.type, barrier.state)
                    for barrier in barriers
                ]

                # Parse the barriers and save them in a dictionary
                devices = {
                    barrier.id: barrier for barrier in parsed_barriers if barrier
                }
                self.organization_id = await barriers[0].get_attr("organization")
            except AuthFailedError as e:
                raise ConfigEntryAuthFailed from e
            except ApiError as e:
                raise UpdateFailed from e
            else:
                self.async_set_updated_data(devices)