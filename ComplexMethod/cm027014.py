async def _add_update_service(self, type_: str, name: str):
            """Add or update a service."""
            service = None
            tries = 0
            while service is None and tries < 4:
                service = await self._aiozc.async_get_service_info(type_, name)
                tries += 1

            if not service:
                _LOGGER.debug("_add_update_service failed to add %s, %s", type_, name)
                return

            _LOGGER.debug("_add_update_service %s %s", name, service)
            service_properties = service.properties

            # We need xa and xp, bail out if either is missing
            if not (xa := service_properties.get(b"xa")):
                _LOGGER.info(
                    "Discovered unsupported Thread router without extended address: %s",
                    service,
                )
                return
            if not (xp := service_properties.get(b"xp")):
                _LOGGER.info(
                    "Discovered unsupported Thread router without extended pan ID: %s",
                    service,
                )
                return

            data = async_discovery_data_from_service(service, xa, xp)
            extended_mac_address = xa.hex()
            if name in self._known_routers and self._known_routers[name] == (
                extended_mac_address,
                data,
            ):
                _LOGGER.debug(
                    "_add_update_service suppressing identical update for %s", name
                )
                return
            self._known_routers[name] = (extended_mac_address, data)
            self._router_discovered(extended_mac_address, data)