async def update_home_devices(self) -> None:
        """Update Home devices (alarm, light, sensor, switch, remote ...)."""
        if not self.home_granted:
            return

        try:
            home_nodes: list[Any] = await self.home.get_home_nodes() or []
        except HttpRequestError:
            self.home_granted = False
            _LOGGER.warning("Home access is not granted")
            return

        new_device = False
        for home_node in home_nodes:
            if home_node["category"] in HOME_COMPATIBLE_CATEGORIES:
                if self.home_devices.get(home_node["id"]) is None:
                    new_device = True
                self.home_devices[home_node["id"]] = home_node

        async_dispatcher_send(self.hass, self.signal_home_device_update)

        if new_device:
            async_dispatcher_send(self.hass, self.signal_home_device_new)