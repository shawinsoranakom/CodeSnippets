async def setup(self, driver: Driver) -> None:
        """Set up devices using the ready driver."""
        self.driver = driver
        controller = driver.controller

        # If opt in preference hasn't been specified yet, we do nothing, otherwise
        # we apply the preference
        if opted_in := self.config_entry.data.get(CONF_DATA_COLLECTION_OPTED_IN):
            await async_enable_statistics(driver)
        elif opted_in is False:
            await driver.async_disable_statistics()

        async def handle_logging_changed(_: Event | None = None) -> None:
            """Handle logging changed event."""
            if LIB_LOGGER.isEnabledFor(logging.DEBUG):
                await async_enable_server_logging_if_needed(
                    self.hass, self.config_entry, driver
                )
            else:
                await async_disable_server_logging_if_needed(
                    self.hass, self.config_entry, driver
                )

        # Set up server logging on setup if needed
        await handle_logging_changed()

        self.config_entry.async_on_unload(
            self.hass.bus.async_listen(EVENT_LOGGING_CHANGED, handle_logging_changed)
        )

        # run discovery on controller node
        if controller.own_node:
            await self.controller_events.async_on_node_added(controller.own_node)

        # run discovery on all other ready nodes
        await asyncio.gather(
            *(
                self.controller_events.async_on_node_added(node)
                for node in controller.nodes.values()
                if node != controller.own_node
            )
        )

        # listen for driver ready event to reload the config entry
        self.config_entry.async_on_unload(
            driver.on(
                "driver ready",
                lambda _: self.hass.config_entries.async_schedule_reload(
                    self.config_entry.entry_id
                ),
            )
        )

        # listen for new nodes being added to the mesh
        self.config_entry.async_on_unload(
            controller.on(
                "node added",
                lambda event: self.hass.async_create_task(
                    self.controller_events.async_on_node_added(event["node"]),
                    eager_start=False,
                ),
            )
        )
        # listen for nodes being removed from the mesh
        # NOTE: This will not remove nodes that were removed when HA was not running
        self.config_entry.async_on_unload(
            controller.on("node removed", self.controller_events.async_on_node_removed)
        )

        # listen for identify events for the controller
        self.config_entry.async_on_unload(
            controller.on("identify", self.controller_events.async_on_identify)
        )

        if (
            old_unique_id := self.config_entry.unique_id
        ) is not None and old_unique_id != (
            new_unique_id := str(driver.controller.home_id)
        ):
            device_registry = dr.async_get(self.hass)
            controller_model = "Unknown model"
            if (
                (own_node := driver.controller.own_node)
                and (
                    controller_device_entry := device_registry.async_get_device(
                        identifiers={get_device_id(driver, own_node)}
                    )
                )
                and (model := controller_device_entry.model)
            ):
                controller_model = model

            # Do not clean up old stale devices if an unknown controller is connected.
            data = {**self.config_entry.data, CONF_KEEP_OLD_DEVICES: True}
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            async_create_issue(
                self.hass,
                DOMAIN,
                f"migrate_unique_id.{self.config_entry.entry_id}",
                data={
                    "config_entry_id": self.config_entry.entry_id,
                    "config_entry_title": self.config_entry.title,
                    "controller_model": controller_model,
                    "new_unique_id": new_unique_id,
                    "old_unique_id": old_unique_id,
                },
                is_fixable=True,
                severity=IssueSeverity.ERROR,
                translation_key="migrate_unique_id",
            )
        else:
            data = self.config_entry.data.copy()
            data.pop(CONF_KEEP_OLD_DEVICES, None)
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            async_delete_issue(
                self.hass, DOMAIN, f"migrate_unique_id.{self.config_entry.entry_id}"
            )

        # Check for nodes that no longer exist and remove them
        stored_devices = dr.async_entries_for_config_entry(
            self.dev_reg, self.config_entry.entry_id
        )
        known_devices = [
            self.dev_reg.async_get_device(identifiers={get_device_id(driver, node)})
            for node in controller.nodes.values()
        ]
        provisioned_devices = [
            self.dev_reg.async_get(entry.additional_properties["device_id"])
            for entry in await controller.async_get_provisioning_entries()
            if entry.additional_properties
            and "device_id" in entry.additional_properties
        ]

        # Devices that are in the device registry that are not known by the controller
        # can be removed
        if not self.config_entry.data.get(CONF_KEEP_OLD_DEVICES):
            for device in stored_devices:
                if device not in known_devices and device not in provisioned_devices:
                    self.dev_reg.async_remove_device(device.id)