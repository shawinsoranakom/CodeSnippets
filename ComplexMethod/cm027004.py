def _create_zwave_listeners(self) -> None:
        """Create Z-Wave JS listeners."""
        self._async_remove()
        # Nodes list can come from different drivers and we will need to listen to
        # server connections for all of them.
        drivers: set[Driver] = set()
        dev_reg = dr.async_get(self._hass)
        if not (
            nodes := async_get_nodes_from_targets(
                self._hass, self._options, dev_reg=dev_reg
            )
        ):
            entry_id = self._options[ATTR_CONFIG_ENTRY_ID]
            entry = self._hass.config_entries.async_get_entry(entry_id)
            assert entry
            client = entry.runtime_data.client
            driver = client.driver
            assert driver
            drivers.add(driver)
            if self._event_source == "controller":
                self._unsubs.append(
                    driver.controller.on(self._event_name, self._async_on_event)
                )
            else:
                self._unsubs.append(driver.on(self._event_name, self._async_on_event))

        for node in nodes:
            driver = node.client.driver
            assert driver is not None  # The node comes from the driver.
            drivers.add(driver)
            device_identifier = get_device_id(driver, node)
            device = dev_reg.async_get_device(identifiers={device_identifier})
            assert device
            # We need to store the device for the callback
            self._unsubs.append(
                node.on(
                    self._event_name,
                    functools.partial(self._async_on_event, device=device),
                )
            )
        self._unsubs.extend(
            async_dispatcher_connect(
                self._hass,
                f"{DOMAIN}_{driver.controller.home_id}_connected_to_server",
                self._create_zwave_listeners,
            )
            for driver in drivers
        )