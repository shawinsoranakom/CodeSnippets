async def _async_update_hosts_info(self) -> dict[str, Device]:
        """Retrieve latest hosts information from the FRITZ!Box."""
        hosts_attributes: list[HostAttributes] = []
        hosts_info: list[HostInfo] = []
        try:
            try:
                hosts_attributes = cast(
                    list[HostAttributes],
                    await self.hass.async_add_executor_job(
                        self.fritz_hosts.get_hosts_attributes
                    ),
                )
            except FritzActionError:
                hosts_info = cast(
                    list[HostInfo],
                    await self.hass.async_add_executor_job(
                        self.fritz_hosts.get_hosts_info
                    ),
                )
        except Exception as ex:
            if not self.hass.is_stopping:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="error_refresh_hosts_info",
                ) from ex

        hosts: dict[str, Device] = {}
        if hosts_attributes:
            for attributes in hosts_attributes:
                if not attributes.get("MACAddress"):
                    continue

                wan_access_result = None
                if (wan_access := attributes.get("X_AVM-DE_WANAccess")) is not None:
                    # wan_access can be "granted", "denied", "unknown" or "error"
                    if "granted" in wan_access:
                        wan_access_result = True
                    elif "denied" in wan_access:
                        wan_access_result = False

                hosts[attributes["MACAddress"]] = Device(
                    name=attributes["HostName"],
                    connected=attributes["Active"],
                    connected_to="",
                    connection_type="",
                    ip_address=attributes["IPAddress"],
                    ssid=None,
                    wan_access=wan_access_result,
                )
        else:
            for info in hosts_info:
                if not info.get("mac"):
                    continue

                if info["ip"]:
                    wan_access_result = await self._async_get_wan_access(info["ip"])
                else:
                    wan_access_result = None

                hosts[info["mac"]] = Device(
                    name=info["name"],
                    connected=info["status"],
                    connected_to="",
                    connection_type="",
                    ip_address=info["ip"],
                    ssid=None,
                    wan_access=wan_access_result,
                )
        return hosts