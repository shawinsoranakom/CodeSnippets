async def async_update(self) -> None:
        """Update state."""
        if (hosts := _get_hosts(self.router)) is None:
            self._available = False
            return
        self._available = True
        host = next(
            (x for x in hosts if x.get("MacAddress") == self._mac_address), None
        )
        self._is_connected = _is_connected(host)
        if host is not None:
            # IpAddress can contain multiple semicolon separated addresses.
            # Pick one for model sanity; e.g. the dhcp component to which it is fed, parses and expects to see just one.
            self._ip_address = (host.get("IpAddress") or "").split(";", 2)[0] or None
            self._hostname = host.get("HostName")
            self._extra_state_attributes = {
                snakecase(k): v
                for k, v in host.items()
                if k
                in {
                    "AddressSource",
                    "AssociatedSsid",
                    "InterfaceType",
                }
            }