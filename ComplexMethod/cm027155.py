async def _async_setup(self) -> None:
        """Set up the coordinator - authenticate and fetch device info."""
        try:
            await self.client.get_device_info()
            system_info_response = await self.client.get_system_info()
        except TeltonikaAuthenticationError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except (ClientResponseError, ContentTypeError) as err:
            if (isinstance(err, ClientResponseError) and err.status in (401, 403)) or (
                isinstance(err, ContentTypeError) and err.status == 403
            ):
                raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
            raise ConfigEntryNotReady(f"Failed to connect to device: {err}") from err
        except TeltonikaConnectionError as err:
            raise ConfigEntryNotReady(f"Failed to connect to device: {err}") from err

        # Store device info for use by entities
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, system_info_response.mnf_info.serial)},
            name=system_info_response.static.device_name,
            manufacturer="Teltonika",
            model=system_info_response.static.model,
            sw_version=system_info_response.static.fw_version,
            serial_number=system_info_response.mnf_info.serial,
            configuration_url=self.base_url,
        )