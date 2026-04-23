async def _async_run_nmap_scan(self):
        """Scan the network for devices and dispatch events."""
        result = await self._hass.async_add_executor_job(self._run_nmap_scan)
        if self._stopping:
            return

        devices = self.devices
        entry_id = self._entry_id
        now = dt_util.now()
        for ipv4, info in result["scan"].items():
            status = info["status"]
            reason = status["reason"]
            if status["state"] != "up":
                self._async_device_offline(ipv4, reason, now)
                continue
            # Mac address only returned if nmap ran as root
            mac = info["addresses"].get(
                "mac"
            ) or await self._hass.async_add_executor_job(
                partial(get_mac_address, ip=ipv4)
            )
            if mac is None:
                self._async_device_offline(ipv4, "No MAC address found", now)
                _LOGGER.warning("No MAC address found for %s", ipv4)
                continue

            formatted_mac = format_mac(mac)

            if formatted_mac in self._mac_exclude:
                _LOGGER.debug("MAC address %s is excluded from tracking", formatted_mac)
                continue

            if (
                devices.config_entry_owner.setdefault(formatted_mac, entry_id)
                != entry_id
            ):
                continue

            hostname = info["hostnames"][0]["name"] if info["hostnames"] else ipv4
            vendor = info.get("vendor", {}).get(mac) or aiooui.get_vendor(mac)
            name = human_readable_name(hostname, vendor, mac)
            device = NmapDevice(
                formatted_mac, hostname, name, ipv4, vendor, reason, now, None
            )

            new = formatted_mac not in devices.tracked
            devices.tracked[formatted_mac] = device
            devices.ipv4_last_mac[ipv4] = formatted_mac
            self._last_results.append(device)

            if new:
                async_dispatcher_send(self._hass, self.signal_device_new, formatted_mac)
            else:
                async_dispatcher_send(
                    self._hass, signal_device_update(formatted_mac), True
                )