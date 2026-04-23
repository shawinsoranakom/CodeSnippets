async def _async_setup(self) -> None:
        """Provide needed data to the device info."""

        about = await asyncio.wait_for(self.device.get_about(), timeout=SETUP_TIMEOUT)
        self.device.mac_address = about["info"]["ifaces"][0]["mac"]
        self.device_info["model"] = about["info"]["model"]
        self.device_info["manufacturer"] = about["info"]["brand"]
        if self.device.mac_address is not None:
            self.device_info[ATTR_IDENTIFIERS] = {
                (DOMAIN, format_mac(iface["mac"]))
                for iface in about["info"]["ifaces"]
                if "mac" in iface and iface["mac"] is not None
            }
            self.device_info[ATTR_CONNECTIONS] = {
                (CONNECTION_NETWORK_MAC, format_mac(iface["mac"]))
                for iface in about["info"]["ifaces"]
                if "mac" in iface and iface["mac"] is not None
            }
            self.unique_id = self.device.mac_address
        elif self.unique_id is not None:
            self.device_info[ATTR_IDENTIFIERS] = {(DOMAIN, self.unique_id)}