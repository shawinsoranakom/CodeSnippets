async def _fetch_device_info(
        self, host: str, port: int | None, noise_psk: str | None
    ) -> str | None:
        """Fetch device info from API and return any errors."""
        zeroconf_instance = await zeroconf.async_get_instance(self.hass)
        cli = APIClient(
            host,
            port or DEFAULT_PORT,
            self._password or "",
            zeroconf_instance=zeroconf_instance,
            noise_psk=noise_psk,
        )
        try:
            await cli.connect()
            self._device_info = await cli.device_info()
            self._connected_address = cli.connected_address
        except InvalidAuthAPIError:
            return ERROR_INVALID_PASSWORD_AUTH
        except RequiresEncryptionAPIError:
            return ERROR_REQUIRES_ENCRYPTION_KEY
        except InvalidEncryptionKeyAPIError as ex:
            if ex.received_name:
                device_name_changed = self._device_name != ex.received_name
                self._device_name = ex.received_name
                if ex.received_mac:
                    self._device_mac = format_mac(ex.received_mac)
                if not self._name or device_name_changed:
                    self._name = ex.received_name
            return ERROR_INVALID_ENCRYPTION_KEY
        except ResolveAPIError:
            return "resolve_error"
        except APIConnectionError:
            return "connection_error"
        finally:
            await cli.disconnect(force=True)
        self._device_mac = format_mac(self._device_info.mac_address)
        self._device_name = self._device_info.name
        self._name = self._device_info.friendly_name or self._device_info.name
        return None