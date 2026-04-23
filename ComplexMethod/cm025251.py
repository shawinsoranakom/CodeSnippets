async def async_scan_devices(self, now: datetime | None = None) -> None:
        """Scan for new network devices."""

        if self.hass.is_stopping:
            ha_is_stopping("scan devices")
            return

        _LOGGER.debug("Checking devices for FRITZ!Box device %s", self.host)
        _default_consider_home = DEFAULT_CONSIDER_HOME.total_seconds()
        if self._options:
            consider_home = self._options.get(
                CONF_CONSIDER_HOME, _default_consider_home
            )
        else:
            consider_home = _default_consider_home

        new_device = False
        hosts = await self._async_update_hosts_info()

        if not self.fritz_status.device_has_mesh_support or (
            self._options
            and self._options.get(CONF_OLD_DISCOVERY, DEFAULT_CONF_OLD_DISCOVERY)
        ):
            _LOGGER.debug(
                "Using old hosts discovery method. (Mesh not supported or user option)"
            )
            self.mesh_role = MeshRoles.NONE
            for mac, info in hosts.items():
                if self.manage_device_info(info, mac, consider_home):
                    new_device = True
            await self.async_send_signal_device_update(new_device)
            return

        try:
            if not (
                topology := await self.hass.async_add_executor_job(
                    self.fritz_hosts.get_mesh_topology
                )
            ) or not isinstance(topology, dict):
                raise Exception("Mesh supported but empty topology reported")  # noqa: TRY002
        except FritzActionError:
            self.mesh_role = MeshRoles.SLAVE
            # Avoid duplicating device trackers
            return

        mesh_intf = {}
        # first get all meshed devices
        for node in topology.get("nodes", []):
            if not node["is_meshed"]:
                continue

            for interf in node["node_interfaces"]:
                int_mac = interf["mac_address"]
                mesh_intf[interf["uid"]] = Interface(
                    device=node["device_name"],
                    mac=int_mac,
                    op_mode=interf.get("op_mode", ""),
                    ssid=interf.get("ssid", ""),
                    type=interf["type"],
                )

                if interf["type"].lower() == "wlan" and interf[
                    "name"
                ].lower().startswith("uplink"):
                    self.mesh_wifi_uplink = True

                if dr.format_mac(int_mac) == self.mac:
                    self.mesh_role = MeshRoles(node["mesh_role"])

        # second get all client devices
        for node in topology.get("nodes", []):
            if node["is_meshed"]:
                continue

            for interf in node["node_interfaces"]:
                dev_mac = interf["mac_address"]

                if dev_mac not in hosts:
                    continue

                dev_info: Device = hosts[dev_mac]

                for link in interf["node_links"]:
                    if link.get("state") != "CONNECTED":
                        continue  # ignore orphan node links

                    intf = mesh_intf.get(link["node_interface_1_uid"])
                    if intf is not None:
                        if intf["op_mode"] == "AP_GUEST":
                            dev_info.wan_access = None

                        dev_info.connected_to = intf["device"]
                        dev_info.connection_type = intf["type"]
                        dev_info.ssid = intf.get("ssid")

                if self.manage_device_info(dev_info, dev_mac, consider_home):
                    new_device = True

        await self.async_send_signal_device_update(new_device)