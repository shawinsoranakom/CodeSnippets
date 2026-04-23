def _async_search_device(self, device_id: str, *, entry_point: bool = True) -> None:
        """Find results for a device."""
        if not (device_entry := self._async_resolve_up_device(device_id)):
            return

        if entry_point:
            # Add labels of this device
            self._add(ItemType.LABEL, device_entry.labels)

        # Automations referencing this device
        self._add(
            ItemType.AUTOMATION,
            automation.automations_with_device(self.hass, device_id),
        )

        # Automations referencing labels assigned to this device
        for label_id in device_entry.labels:
            self._add(
                ItemType.AUTOMATION,
                automation.automations_with_label(self.hass, label_id),
            )

        if device_entry.area_id:
            # Automations referencing this device via its area
            self._add(
                ItemType.AUTOMATION,
                automation.automations_with_area(self.hass, device_entry.area_id),
            )
            # Automations referencing this device via its areas floor
            if area_entry := self._area_registry.async_get_area(device_entry.area_id):
                if area_entry.floor_id:
                    self._add(
                        ItemType.AUTOMATION,
                        automation.automations_with_floor(
                            self.hass, area_entry.floor_id
                        ),
                    )

        # Scripts referencing this device
        self._add(ItemType.SCRIPT, script.scripts_with_device(self.hass, device_id))

        # Entities of this device
        for entity_entry in er.async_entries_for_device(
            self._entity_registry, device_id
        ):
            self._add(ItemType.ENTITY, entity_entry.entity_id)
            # Add all entity information as well
            self._async_search_entity(entity_entry.entity_id, entry_point=False)