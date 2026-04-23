async def async_update(self) -> None:
        """Get updated data from SimpliSafe."""

        async def async_update_system(system: SystemType) -> None:
            """Update a single system and process notifications."""
            await system.async_update(cached=system.version != 3)
            self._async_process_new_notifications(system)

        tasks = [async_update_system(system) for system in self.systems.values()]

        try:
            # Gather all system updates; exceptions will propagate
            await asyncio.gather(*tasks)
        except InvalidCredentialsError as err:
            # Stop websocket immediately on auth failure
            if self._websocket_task:
                LOGGER.debug("Cancelling websocket loop due to invalid credentials")
                await self._async_cancel_websocket_loop()
            # Signal HA that credentials are invalid; user intervention is required
            raise ConfigEntryAuthFailed("Invalid credentials") from err
        except RequestError as err:
            # Cloud-level request errors: wrap aiohttp errors
            if self._websocket_task:
                LOGGER.debug("Cancelling websocket loop due to request error")
                await self._async_cancel_websocket_loop()
            raise UpdateFailed(
                f"Request error while updating all systems: {err}"
            ) from err
        except EndpointUnavailableError as err:
            # Currently not raised by the API; included for future-proofing.
            # Informational per-system (e.g., user plan restrictions)
            LOGGER.debug("Endpoint unavailable: %s", err)
        except SimplipyError as err:
            # Any other SimplipyError not caught per-system
            raise UpdateFailed(f"SimpliSafe error while updating: {err}") from err
        else:
            # Successful update, try to restart websocket if necessary
            self._async_start_websocket_if_needed()