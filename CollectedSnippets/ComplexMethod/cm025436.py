async def async_update(self) -> None:
        """Update entity status."""
        if not self.available:
            return
        _LOGGER.debug("Updating %s camera", self.name)
        try:
            if self._brand is None:
                resp = await self._api.async_vendor_information
                _LOGGER.debug("Assigned brand=%s", resp)
                if resp:
                    self._brand = resp
                else:
                    self._brand = "unknown"
            if self._model is None:
                resp = await self._api.async_device_type
                _LOGGER.debug("Assigned model=%s", resp)
                if resp:
                    self._model = resp
                else:
                    self._model = "unknown"
            if self._attr_unique_id is None:
                serial_number = (await self._api.async_serial_number).strip()
                if serial_number:
                    self._attr_unique_id = (
                        f"{serial_number}-{self._resolution}-{self._channel}"
                    )
                    _LOGGER.debug("Assigned unique_id=%s", self._attr_unique_id)
            if self._rtsp_url is None:
                self._rtsp_url = await self._api.async_rtsp_url(typeno=self._resolution)

            (
                self._attr_is_streaming,
                self._is_recording,
                self._motion_detection_enabled,
                self._audio_enabled,
                self._motion_recording_enabled,
                self._color_bw,
            ) = await asyncio.gather(
                self._async_get_video(),
                self._async_get_recording(),
                self._async_get_motion_detection(),
                self._async_get_audio(),
                self._async_get_motion_recording(),
                self._async_get_color_mode(),
            )
        except AmcrestError as error:
            log_update_error(_LOGGER, "get", self.name, "camera attributes", error)