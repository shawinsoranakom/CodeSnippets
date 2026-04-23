async def _async_start_upnp_servers(self, event: Event) -> None:
        """Start the UPnP/SSDP servers."""
        # Update UDN with our instance UDN.
        udn = await self._async_get_instance_udn()
        system_info = await async_get_system_info(self.hass)
        model_name = system_info["installation_type"]
        try:
            presentation_url = get_url(self.hass, allow_ip=True, prefer_external=False)
        except NoURLAvailableError:
            _LOGGER.warning(
                "Could not set up UPnP/SSDP server, as a presentation URL could"
                " not be determined; Please configure your internal URL"
                " in the Home Assistant general configuration"
            )
            return

        serial_number = await async_get_instance_id(self.hass)
        HassUpnpServiceDevice.DEVICE_DEFINITION = (
            HassUpnpServiceDevice.DEVICE_DEFINITION._replace(
                udn=udn,
                friendly_name=f"{self.hass.config.location_name} (Home Assistant)",
                model_name=model_name,
                presentation_url=presentation_url,
                serial_number=serial_number,
            )
        )

        # Update icon URLs.
        for index, icon in enumerate(HassUpnpServiceDevice.DEVICE_DEFINITION.icons):
            new_url = urljoin(presentation_url, icon.url)
            HassUpnpServiceDevice.DEVICE_DEFINITION.icons[index] = icon._replace(
                url=new_url
            )

        # Start a server on all source IPs.
        boot_id = int(time())
        # We use an ExitStack to ensure that all sockets are closed.
        # The socket is created in _async_find_next_available_port,
        # and should be kept open until UpnpServer is started to
        # keep the kernel from reassigning the port.
        with ExitStack() as stack:
            for source_ip in await async_build_source_set(self.hass):
                source_ip_str = str(source_ip)
                if source_ip.version == 6:
                    source_ip = cast(IPv6Address, source_ip)
                    assert source_ip.scope_id is not None
                    source_tuple: AddressTupleVXType = (
                        source_ip_str,
                        0,
                        0,
                        int(source_ip.scope_id),
                    )
                else:
                    source_tuple = (source_ip_str, 0)
                source, target = determine_source_target(source_tuple)
                source = fix_ipv6_address_scope_id(source) or source
                http_port, http_socket = await _async_find_next_available_port(source)
                stack.enter_context(http_socket)
                _LOGGER.debug(
                    "Binding UPnP HTTP server to: %s:%s", source_ip, http_port
                )
                self._upnp_servers.append(
                    UpnpServer(
                        source=source,
                        target=target,
                        http_port=http_port,
                        server_device=HassUpnpServiceDevice,
                        boot_id=boot_id,
                    )
                )
            results = await asyncio.gather(
                *(upnp_server.async_start() for upnp_server in self._upnp_servers),
                return_exceptions=True,
            )
        failed_servers = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                _LOGGER.debug(
                    "Failed to setup server for %s: %s",
                    self._upnp_servers[idx].source,
                    result,
                )
                failed_servers.append(self._upnp_servers[idx])
        for server in failed_servers:
            self._upnp_servers.remove(server)