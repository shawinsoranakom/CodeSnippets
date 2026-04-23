async def _async_update_data(self) -> HomeConnectApplianceData:
        """Fetch data from Home Connect."""
        while True:
            try:
                try:
                    self.data.info.connected = (
                        await self.client.get_specific_appliance(self.data.info.ha_id)
                    ).connected
                except HomeConnectError:
                    self.data.info.connected = False
                    raise

                await self.get_appliance_data()
            except TooManyRequestsError as err:
                delay = err.retry_after or API_DEFAULT_RETRY_AFTER
                _LOGGER.warning(
                    "Rate limit exceeded, retrying in %s seconds: %s",
                    delay,
                    err,
                )
                await asyncio_sleep(delay)
            except UnauthorizedError as error:
                # Reauth flow need to be started explicitly as
                # we don't use the default config entry coordinator.
                self._config_entry.async_start_reauth(self.hass)
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="auth_error",
                    translation_placeholders=get_dict_from_home_connect_error(error),
                ) from error
            except HomeConnectError as error:
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="fetch_api_error",
                    translation_placeholders=get_dict_from_home_connect_error(error),
                ) from error
            else:
                break

        for (
            listener,
            context,
        ) in self.global_listeners.values():
            assert isinstance(context, tuple)
            if EventKey.BSH_COMMON_APPLIANCE_PAIRED in context:
                listener()

        return self.data