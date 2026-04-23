def async_on_node_removed(self, event: dict) -> None:
        """Handle node removed event."""
        node: ZwaveNode = event["node"]
        reason: RemoveNodeReason = event["reason"]
        # grab device in device registry attached to this node
        dev_id = get_device_id(self.driver_events.driver, node)
        device = self.dev_reg.async_get_device(identifiers={dev_id})
        # We assert because we know the device exists
        assert device
        if reason in (RemoveNodeReason.REPLACED, RemoveNodeReason.PROXY_REPLACED):
            self.discovered_value_ids.pop(device.id, None)

            async_dispatcher_send(
                self.hass,
                (
                    f"{DOMAIN}_"
                    f"{get_valueless_base_unique_id(self.driver_events.driver, node)}_"
                    "remove_entity"
                ),
            )
            # We don't want to remove the device so we can keep the user customizations
            return

        if reason == RemoveNodeReason.RESET:
            device_name = device.name_by_user or device.name or f"Node {node.node_id}"
            identifier = get_network_identifier_for_notification(
                self.hass, self.config_entry, self.driver_events.driver.controller
            )
            notification_msg = (
                f"`{device_name}` has been factory reset "
                "and removed from the Z-Wave network"
            )
            if identifier:
                # Remove trailing comma if it's there
                if identifier[-1] == ",":
                    identifier = identifier[:-1]
                notification_msg = f"{notification_msg} {identifier}."
            else:
                notification_msg = f"{notification_msg}."
            async_create(
                self.hass,
                notification_msg,
                "Device Was Factory Reset!",
                f"{DOMAIN}.node_reset_and_removed.{dev_id[1]}",
            )

        self.node_events.value_updates_disc_info.pop(node.node_id, None)
        self.remove_device(device)