async def _async_update_data(self) -> bool:
        """Update data device by device."""
        try:
            if (
                self.ayla_api.token_expiring_soon
                or datetime.now()
                > self.ayla_api.auth_expiration - timedelta(seconds=600)
            ):
                await self.ayla_api.async_refresh_auth()

            all_vacuums = await self.ayla_api.async_list_devices()
            self._online_dsns = {
                v["dsn"]
                for v in all_vacuums
                if v["connection_status"] == "Online" and v["dsn"] in self.shark_vacs
            }

            LOGGER.debug("Updating sharkiq data")
            online_vacs = (self.shark_vacs[dsn] for dsn in self.online_dsns)
            await asyncio.gather(*(self._async_update_vacuum(v) for v in online_vacs))
        except (
            SharkIqAuthError,
            SharkIqNotAuthedError,
            SharkIqAuthExpiringError,
        ) as err:
            LOGGER.debug("Bad auth state.  Attempting re-auth", exc_info=err)
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            LOGGER.exception("Unexpected error updating SharkIQ.  Attempting re-auth")
            raise UpdateFailed(err) from err

        return True