def async_process_client(
        self,
        ip_address: str,
        hostname: str,
        unformatted_mac_address: str,
        force: bool = False,
    ) -> None:
        """Process a client."""
        if (made_ip_address := cached_ip_addresses(ip_address)) is None:
            # Ignore invalid addresses
            _LOGGER.debug("Ignoring invalid IP Address: %s", ip_address)
            return

        if (
            made_ip_address.is_link_local
            or made_ip_address.is_loopback
            or made_ip_address.is_unspecified
        ):
            # Ignore self assigned addresses, loopback, invalid
            return

        formatted_mac = format_mac(unformatted_mac_address)
        # Historically, the MAC address was formatted without colons
        # and since all consumers of this data are expecting it to be
        # formatted without colons we will continue to do so
        mac_address = formatted_mac.replace(":", "")
        compressed_ip_address = made_ip_address.compressed

        current_data = self._address_data.get(mac_address)
        if (
            not force
            and current_data
            and current_data[IP_ADDRESS] == compressed_ip_address
            and current_data[HOSTNAME].startswith(hostname)
        ):
            # If the address data is the same no need
            # to process it
            return

        data: DHCPAddressData = {IP_ADDRESS: compressed_ip_address, HOSTNAME: hostname}
        self._address_data[mac_address] = data

        lowercase_hostname = hostname.lower()
        uppercase_mac = mac_address.upper()

        _LOGGER.debug(
            "Processing updated address data for %s: mac=%s hostname=%s",
            ip_address,
            uppercase_mac,
            lowercase_hostname,
        )

        matched_domains: set[str] = set()
        matchers = self._integration_matchers
        registered_devices_domains = matchers.registered_devices_domains

        dev_reg = dr.async_get(self.hass)
        if device := dev_reg.async_get_device(
            connections={(CONNECTION_NETWORK_MAC, formatted_mac)}
        ):
            for entry_id in device.config_entries:
                if (
                    entry := self.hass.config_entries.async_get_entry(entry_id)
                ) and entry.domain in registered_devices_domains:
                    matched_domains.add(entry.domain)

        oui = uppercase_mac[:6]
        lowercase_hostname_first_char = (
            lowercase_hostname[0] if len(lowercase_hostname) else ""
        )
        for matcher in itertools.chain(
            matchers.no_oui_matchers.get(lowercase_hostname_first_char, ()),
            matchers.oui_matchers.get(oui, ()),
        ):
            domain = matcher["domain"]
            if (
                matcher_hostname := matcher.get(HOSTNAME)
            ) is not None and not _memorized_fnmatch(
                lowercase_hostname, matcher_hostname
            ):
                continue

            _LOGGER.debug("Matched %s against %s", data, matcher)
            matched_domains.add(domain)

        if self._callbacks:
            address_data = {mac_address: data}
            for callback_ in self._callbacks:
                callback_(address_data)

        service_info: _DhcpServiceInfo | None = None
        if not matched_domains:
            return
        service_info = _DhcpServiceInfo(
            ip=ip_address,
            hostname=lowercase_hostname,
            macaddress=mac_address,
        )
        discovery_key = DiscoveryKey(
            domain=DOMAIN,
            key=mac_address,
            version=1,
        )
        for domain in matched_domains:
            discovery_flow.async_create_flow(
                self.hass,
                domain,
                {"source": config_entries.SOURCE_DHCP},
                service_info,
                discovery_key=discovery_key,
            )