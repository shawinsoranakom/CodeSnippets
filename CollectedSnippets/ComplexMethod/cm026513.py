async def _validate_host(
        self, host: str
    ) -> tuple[str | None, APIVersionResponse | None, dict[str, str] | None]:
        """Validate the host and return (serial_number, api_versions, errors)."""
        client = PooldoseClient(host, websession=async_get_clientsession(self.hass))
        client_status = await client.connect()
        if client_status == RequestStatus.HOST_UNREACHABLE:
            return None, None, {"base": "cannot_connect"}
        if client_status == RequestStatus.PARAMS_FETCH_FAILED:
            return None, None, {"base": "params_fetch_failed"}
        if client_status != RequestStatus.SUCCESS:
            return None, None, {"base": "cannot_connect"}

        api_status, api_versions = client.check_apiversion_supported()
        if api_status == RequestStatus.NO_DATA:
            return None, None, {"base": "api_not_set"}
        if api_status == RequestStatus.API_VERSION_UNSUPPORTED:
            return None, api_versions, {"base": "api_not_supported"}

        device_info = client.device_info
        if not device_info:
            return None, None, {"base": "no_device_info"}
        serial_number = device_info.get("SERIAL_NUMBER")
        if not serial_number:
            return None, None, {"base": "no_serial_number"}

        return serial_number, None, None