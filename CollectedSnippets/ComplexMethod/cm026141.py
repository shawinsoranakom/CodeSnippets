async def _async_start_ssdp_listeners(self) -> None:
        """Start the SSDP Listeners."""
        # Devices are shared between all sources.
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
            self._ssdp_listeners.append(
                SsdpListener(
                    callback=self._ssdp_listener_callback,
                    source=source,
                    target=target,
                    device_tracker=self._device_tracker,
                )
            )
        results = await asyncio.gather(
            *(
                create_eager_task(listener.async_start())
                for listener in self._ssdp_listeners
            ),
            return_exceptions=True,
        )
        failed_listeners = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                _LOGGER.debug(
                    "Failed to setup listener for %s: %s",
                    self._ssdp_listeners[idx].source,
                    result,
                )
                failed_listeners.append(self._ssdp_listeners[idx])
        for listener in failed_listeners:
            self._ssdp_listeners.remove(listener)