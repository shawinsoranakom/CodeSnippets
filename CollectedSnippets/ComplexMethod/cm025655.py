async def _async_update_data(self) -> dict[str, GwEntityData]:
        """Fetch data from Plugwise."""
        try:
            if not self._connected:
                await self._connect()
            data = await self.api.async_update()
        except ConnectionFailedError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="failed_to_connect",
            ) from err
        except InvalidAuthentication as err:
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="authentication_failed",
            ) from err
        except InvalidSetupError as err:
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="invalid_setup",
            ) from err
        except (InvalidXMLError, ResponseError) as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="response_error",
            ) from err
        except PlugwiseError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="data_incomplete_or_missing",
            ) from err
        except UnsupportedDeviceError as err:
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="unsupported_firmware",
            ) from err

        self._add_remove_devices(data)
        self._update_device_firmware(data)
        return data