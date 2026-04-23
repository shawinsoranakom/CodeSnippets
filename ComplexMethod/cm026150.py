def update_devices(self) -> None:
        """Get list of devices with latest status."""
        arp_devices = {}
        device_list = {}
        wireless_devices = {}
        try:
            self.all_devices = self.get_list_from_interface(DHCP)
            if self.support_capsman:
                _LOGGER.debug("Hub is a CAPSman manager")
                device_list = wireless_devices = self.get_list_from_interface(CAPSMAN)
            elif self.support_wireless:
                _LOGGER.debug("Hub supports wireless Interface")
                device_list = wireless_devices = self.get_list_from_interface(WIRELESS)
            elif self.support_wifiwave2:
                _LOGGER.debug("Hub supports wifiwave2 Interface")
                device_list = wireless_devices = self.get_list_from_interface(WIFIWAVE2)
            elif self.support_wifi:
                _LOGGER.debug("Hub supports wifi Interface")
                device_list = wireless_devices = self.get_list_from_interface(WIFI)

            if not device_list or self.force_dhcp:
                device_list = self.all_devices
                _LOGGER.debug("Falling back to DHCP for scanning devices")

            if self.arp_enabled:
                _LOGGER.debug("Using arp-ping to check devices")
                arp_devices = self.get_list_from_interface(ARP)

            # get new hub firmware version if updated
            self.firmware = self.get_info(ATTR_FIRMWARE)

        except CannotConnect as err:
            raise UpdateFailed from err
        except LoginError as err:
            raise ConfigEntryAuthFailed from err

        if not device_list:
            return

        for mac, params in device_list.items():
            if mac not in self.devices:
                self.devices[mac] = Device(mac, self.all_devices.get(mac, {}))
            else:
                self.devices[mac].update(params=self.all_devices.get(mac, {}))

            if mac in wireless_devices:
                # if wireless is supported then wireless_params are params
                self.devices[mac].update(
                    wireless_params=wireless_devices[mac], active=True
                )
                continue
            # for wired devices or when forcing dhcp check for active-address
            if not params.get("active-address"):
                self.devices[mac].update(active=False)
                continue
            # ping check the rest of active devices if arp ping is enabled
            active = True
            if self.arp_enabled and mac in arp_devices:
                active = self.do_arp_ping(
                    str(params.get("active-address")),
                    str(arp_devices[mac].get("interface")),
                )
            self.devices[mac].update(active=active)