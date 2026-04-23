async def _async_update_data(self) -> None:
        """Fetch all device data from the api."""
        device = self.device
        if (
            device.host_firmware_version is None
            or device.product is None
            or device.group is None
        ):
            await self._async_populate_device_info()

        num_zones = self.get_number_of_zones()
        features = lifx_features(self.device)
        update_rssi = self._update_rssi
        methods: list[Callable] = [self.device.get_color]
        if update_rssi:
            methods.append(self.device.get_wifiinfo)
        if self.is_matrix:
            methods.extend(
                [
                    self.device.get_tile_effect,
                    self.device.get_device_chain,
                ]
            )
            methods.extend(self._async_build_get64_update_requests())
        if self.is_extended_multizone:
            methods.append(self.device.get_extended_color_zones)
        elif self.is_legacy_multizone:
            methods.extend(self._async_build_color_zones_update_requests())
        if self.is_extended_multizone or self.is_legacy_multizone:
            methods.append(self.device.get_multizone_effect)
        if features["hev"]:
            methods.append(self.device.get_hev_cycle)
        if features["infrared"]:
            methods.append(self.device.get_infrared)

        responses = await async_multi_execute_lifx_with_retries(
            methods, MAX_ATTEMPTS_PER_UPDATE_REQUEST_MESSAGE, MAX_UPDATE_TIME
        )
        # device.mac_addr is not the mac_address, its the serial number
        if device.mac_addr == TARGET_ANY:
            device.mac_addr = responses[0].target_addr

        if update_rssi:
            # We always send the rssi request second
            self._rssi = int(floor(10 * log10(responses[1].signal) + 0.5))

        if self.is_matrix or self.is_extended_multizone or self.is_legacy_multizone:
            self.active_effect = FirmwareEffect[self.device.effect.get("effect", "OFF")]

        if self.is_legacy_multizone and num_zones != self.get_number_of_zones():
            # The number of zones has changed so we need
            # to update the zones again. This happens rarely.
            await self.async_get_color_zones()