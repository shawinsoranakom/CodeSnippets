async def async_get_adapter_indexes(self) -> list[int] | None:
        """Get the adapter indexes."""
        adapters = await network.async_get_adapters(self.hass)
        if network.async_only_default_interface_enabled(adapters):
            return None
        return [
            adapter["index"]
            for adapter in adapters
            if (
                adapter["enabled"]
                and adapter["index"] is not None
                and adapter["ipv4"]
                and (
                    addresses := [IPv4Address(ip["address"]) for ip in adapter["ipv4"]]
                )
                and any(
                    ip for ip in addresses if not ip.is_loopback and not ip.is_global
                )
            )
        ]