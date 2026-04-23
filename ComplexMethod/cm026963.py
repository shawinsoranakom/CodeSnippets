async def async_check_pre_provisioned_device(self, node: ZwaveNode) -> None:
        """Check if the node was pre-provisioned and update the device registry."""
        provisioning_entry = (
            await self.driver_events.driver.controller.async_get_provisioning_entry(
                node.node_id
            )
        )
        if (
            provisioning_entry
            and provisioning_entry.additional_properties
            and "device_id" in provisioning_entry.additional_properties
            and (
                pre_provisioned_device := self.dev_reg.async_get(
                    provisioning_entry.additional_properties["device_id"]
                )
            )
            and (dsk_identifier := (DOMAIN, f"provision_{provisioning_entry.dsk}"))
            in pre_provisioned_device.identifiers
        ):
            driver = self.driver_events.driver
            device_id = get_device_id(driver, node)
            device_id_ext = get_device_id_ext(driver, node)
            new_identifiers = pre_provisioned_device.identifiers.copy()
            new_identifiers.remove(dsk_identifier)
            new_identifiers.add(device_id)
            if device_id_ext:
                new_identifiers.add(device_id_ext)

            if self.dev_reg.async_get_device(identifiers=new_identifiers):
                # If a device entry is registered with the node ID based identifiers,
                # just remove the device entry with the DSK identifier.
                self.dev_reg.async_update_device(
                    pre_provisioned_device.id,
                    remove_config_entry_id=self.config_entry.entry_id,
                )
            else:
                # Add the node ID based identifiers to the device entry
                # with the DSK identifier and remove the DSK identifier.
                self.dev_reg.async_update_device(
                    pre_provisioned_device.id,
                    new_identifiers=new_identifiers,
                )