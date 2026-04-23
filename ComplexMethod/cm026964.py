async def async_register_node_in_dev_reg(self, node: ZwaveNode) -> dr.DeviceEntry:
        """Register node in dev reg."""
        driver = self.driver_events.driver
        device_id = get_device_id(driver, node)
        device_id_ext = get_device_id_ext(driver, node)
        node_id_device = self.dev_reg.async_get_device(identifiers={device_id})
        via_identifier = None
        controller = driver.controller
        # Get the controller node device ID if this node is not the controller
        if controller.own_node and controller.own_node != node:
            via_identifier = get_device_id(driver, controller.own_node)

        if device_id_ext:
            # If there is a device with this node ID but with a different hardware
            # signature, remove the node ID based identifier from it. The hardware
            # signature can be different for one of two reasons: 1) in the ideal
            # scenario, the node was replaced with a different node that's a different
            # device entirely, or 2) the device erroneously advertised the wrong
            # hardware identifiers (this is known to happen due to poor RF conditions).
            # While we would like to remove the old device automatically for case 1, we
            # have no way to distinguish between these reasons so we leave it up to the
            # user to remove the old device manually.
            if (
                node_id_device
                and len(node_id_device.identifiers) == 2
                and device_id_ext not in node_id_device.identifiers
            ):
                new_identifiers = node_id_device.identifiers.copy()
                new_identifiers.remove(device_id)
                self.dev_reg.async_update_device(
                    node_id_device.id, new_identifiers=new_identifiers
                )
            # If there is an orphaned device that already exists with this hardware
            # based identifier, add the node ID based identifier to the orphaned
            # device.
            if (
                hardware_device := self.dev_reg.async_get_device(
                    identifiers={device_id_ext}
                )
            ) and len(hardware_device.identifiers) == 1:
                new_identifiers = hardware_device.identifiers.copy()
                new_identifiers.add(device_id)
                self.dev_reg.async_update_device(
                    hardware_device.id, new_identifiers=new_identifiers
                )
            ids = {device_id, device_id_ext}
        else:
            ids = {device_id}

        device = self.dev_reg.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers=ids,
            sw_version=node.firmware_version,
            name=node.name or node.device_config.description or f"Node {node.node_id}",
            model=node.device_config.label,
            manufacturer=node.device_config.manufacturer,
            suggested_area=node.location or UNDEFINED,
            via_device=via_identifier,
        )

        async_dispatcher_send(self.hass, EVENT_DEVICE_ADDED_TO_REGISTRY, device)

        return device