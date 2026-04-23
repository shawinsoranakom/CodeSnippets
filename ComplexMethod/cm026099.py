async def _async_get_and_check_device_info(self) -> bool:
        """Try to get the device info."""
        result = await self._async_load_device_info()
        if result not in SUCCESSFUL_RESULTS:
            raise AbortFlow(result)
        if not (info := self._device_info):
            return False
        dev_info = info.get("device", {})
        assert dev_info is not None
        if (device_type := dev_info.get("type")) != "Samsung SmartTV":
            LOGGER.debug(
                "Host:%s has type: %s which is not supported", self._host, device_type
            )
            raise AbortFlow(RESULT_NOT_SUPPORTED)
        self._model = dev_info.get("modelName")
        name = dev_info.get("name")
        self._name = name.replace("[TV] ", "") if name else device_type
        self._title = f"{self._name} ({self._model})"
        self._udn = _strip_uuid(dev_info.get("udn", info["id"]))
        if mac := mac_from_device_info(info):
            # Samsung sometimes returns a value of "none" for the mac address
            # this should be ignored - but also shouldn't trigger getmac
            if mac != "none":
                self._mac = mac
        elif mac := await self.hass.async_add_executor_job(
            partial(getmac.get_mac_address, ip=self._host)
        ):
            self._mac = mac
        return True