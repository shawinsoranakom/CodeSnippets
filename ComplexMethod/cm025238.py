async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        name = discovery_info.name
        self.host = discovery_info.host
        self.mac = discovery_info.properties.get("mac")
        if self.mac is None:
            poch = discovery_info.properties.get("poch", "")
            if (result := search(r"mac=\w+", poch)) is not None:
                self.mac = result.group(0).split("=")[1]

        if not name or not self.host or not self.mac:
            return self.async_abort(reason="not_xiaomi_miio")

        self.mac = format_mac(self.mac)

        # Check which device is discovered.
        for gateway_model in MODELS_GATEWAY:
            if name.startswith(gateway_model.replace(".", "-")):
                unique_id = self.mac
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured({CONF_HOST: self.host})

                self.context.update(
                    {"title_placeholders": {"name": f"Gateway {self.host}"}}
                )

                return await self.async_step_cloud()

        for device_model in MODELS_ALL_DEVICES:
            if name.startswith(device_model.replace(".", "-")):
                unique_id = self.mac
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured({CONF_HOST: self.host})

                self.context.update(
                    {"title_placeholders": {"name": f"{device_model} {self.host}"}}
                )

                return await self.async_step_cloud()

        # Discovered device is not yet supported
        _LOGGER.debug(
            "Not yet supported Xiaomi Miio device '%s' discovered with host %s",
            name,
            self.host,
        )
        return self.async_abort(reason="not_xiaomi_miio")