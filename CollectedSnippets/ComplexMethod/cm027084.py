def _async_discover_devices(self) -> None:
        current_addresses = self._async_current_ids(include_ignore=False)
        for connectable in (True, False):
            for discovery_info in async_discovered_service_info(self.hass, connectable):
                address = discovery_info.address
                if (
                    format_unique_id(address) in current_addresses
                    or address in self._discovered_advs
                ):
                    continue
                parsed = parse_advertisement_data(
                    discovery_info.device, discovery_info.advertisement
                )
                if not parsed:
                    continue
                model_name = parsed.data.get("modelName")
                if (
                    discovery_info.connectable
                    and model_name in CONNECTABLE_SUPPORTED_MODEL_TYPES
                ) or model_name in NON_CONNECTABLE_SUPPORTED_MODEL_TYPES:
                    self._discovered_advs[address] = parsed

        if not self._discovered_advs:
            raise AbortFlow("no_devices_found")