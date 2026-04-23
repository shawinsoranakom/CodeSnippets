def update(self) -> None:
        """Refresh key device data."""
        if not self.session:
            self.force_idle()
            if not self.device:
                self._attr_available = False
                return

        self._attr_available = True

        try:
            device_url = self.device.url("/")
        except plexapi.exceptions.BadRequest:
            device_url = "127.0.0.1"
        if "127.0.0.1" in device_url:
            self.device.proxyThroughServer()
        self._device_protocol_capabilities = self.device.protocolCapabilities

        device: PlexClient
        for device in filter(None, [self.device, self.session_device]):
            self.device_make = self.device_make or device.device
            self.device_platform = self.device_platform or device.platform
            self.device_product = self.device_product or device.product
            self.device_title = self.device_title or device.title
            self.device_version = self.device_version or device.version

        name_parts = [self.device_product, self.device_title or self.device_platform]
        if (self.device_product in COMMON_PLAYERS) and self.device_make:
            # Add more context in name for likely duplicates
            name_parts.append(self.device_make)
        if self.username and self.username != self.plex_server.owner:
            # Prepend username for shared/managed clients
            name_parts.insert(0, self.username)
        self._attr_name = NAME_FORMAT.format(" - ".join(name_parts))