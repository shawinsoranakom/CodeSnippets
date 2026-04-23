async def async_on_node_ready(self, node: ZwaveNode) -> None:
        """Handle node ready event."""
        LOGGER.debug("Processing node %s", node)
        # register (or update) node in device registry
        device = await self.controller_events.async_register_node_in_dev_reg(node)

        # Remove any old value ids if this is a reinterview.
        self.controller_events.discovered_value_ids.pop(device.id, None)

        # Store the discovery info so it can be reused when re-discovering entities
        value_updates_disc_info: dict[str, PlatformZwaveDiscoveryInfo] = {}
        self.value_updates_disc_info[node.node_id] = value_updates_disc_info

        # run discovery on all node values and create/update entities
        for disc_info in async_discover_node_values(
            node, device, self.controller_events.discovered_value_ids
        ):
            self.async_handle_discovery_info(device, disc_info, value_updates_disc_info)

        # add listeners to handle new values that get added later
        for event in (EVENT_VALUE_ADDED, EVENT_VALUE_UPDATED, EVENT_METADATA_UPDATED):
            self.config_entry.async_on_unload(
                node.on(
                    event,
                    lambda event: self.async_on_value_added(
                        value_updates_disc_info, event["value"]
                    ),
                )
            )

        # add listener for stateless node value notification events
        self.config_entry.async_on_unload(
            node.on(
                "value notification",
                lambda event: self.async_on_value_notification(
                    event["value_notification"]
                ),
            )
        )

        # add listener for stateless node notification events
        self.config_entry.async_on_unload(
            node.on("notification", self.async_on_notification)
        )

        # Create a firmware update entity for each device that
        # supports firmware updates
        controller = self.controller_events.driver_events.driver.controller
        if (
            not (is_controller_node := node.is_controller_node)
            and any(
                cc.id == CommandClass.FIRMWARE_UPDATE_MD.value
                for cc in node.command_classes
            )
        ) or (
            is_controller_node
            and (sdk_version := controller.sdk_version) is not None
            and sdk_version >= MIN_CONTROLLER_FIRMWARE_SDK_VERSION
        ):
            async_dispatcher_send(
                self.hass,
                f"{DOMAIN}_{self.config_entry.entry_id}_add_firmware_update_entity",
                node,
            )

        # After ensuring the node is set up in HA, we should check if the node's
        # device config has changed, and if so, issue a repair registry entry for a
        # possible reinterview
        if not node.is_controller_node:
            issue_id = f"device_config_file_changed.{device.id}"
            if await node.async_has_device_config_changed():
                device_name = device.name_by_user or device.name or "Unnamed device"
                async_create_issue(
                    self.hass,
                    DOMAIN,
                    issue_id,
                    data={"device_id": device.id, "device_name": device_name},
                    is_fixable=True,
                    is_persistent=False,
                    translation_key="device_config_file_changed",
                    translation_placeholders={"device_name": device_name},
                    severity=IssueSeverity.WARNING,
                )
            else:
                # Clear any existing repair issue if the device config is not considered
                # changed. This can happen when the original issue was created by
                # an upstream bug, or the change has been reverted.
                async_delete_issue(self.hass, DOMAIN, issue_id)