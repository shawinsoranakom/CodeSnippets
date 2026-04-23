async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            discovery = self._discovered_devices[address]

            if discovery.device.firmware.need_firmware_upgrade:
                return self.async_abort(reason="firmware_upgrade_required")

            self.context["title_placeholders"] = {
                "name": discovery.name,
            }

            self._discovered_device = discovery

            return self.async_create_entry(
                title=discovery.name,
                data={DEVICE_MODEL: discovery.device.model.value},
            )

        current_addresses = self._async_current_ids(include_ignore=False)
        devices: list[BluetoothServiceInfoBleak] = []
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue
            if MFCT_ID not in discovery_info.manufacturer_data:
                continue
            if not any(uuid in SERVICE_UUIDS for uuid in discovery_info.service_uuids):
                _LOGGER.debug(
                    "Skipping unsupported device: %s (%s)", discovery_info.name, address
                )
                continue
            devices.append(discovery_info)

        for discovery_info in devices:
            address = discovery_info.address
            data = AirthingsBluetoothDeviceData(logger=_LOGGER)
            try:
                device = await self._get_device(data, discovery_info)
            except AirthingsDeviceUpdateError:
                _LOGGER.error(
                    "Error connecting to and getting data from %s (%s)",
                    discovery_info.name,
                    discovery_info.address,
                )
                continue
            except UnsupportedDeviceError:
                _LOGGER.debug(
                    "Skipping unsupported device: %s (%s)",
                    discovery_info.name,
                    discovery_info.address,
                )
                continue
            except Exception:
                _LOGGER.exception("Unknown error occurred")
                return self.async_abort(reason="unknown")
            name = get_name(device)
            _LOGGER.debug("Discovered Airthings device: %s (%s)", name, address)
            self._discovered_devices[address] = Discovery(
                name, discovery_info, device, data
            )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        titles = {
            address: get_name(discovery.device)
            for (address, discovery) in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(titles),
                },
            ),
        )