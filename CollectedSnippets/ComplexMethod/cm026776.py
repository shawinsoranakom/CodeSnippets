def _async_search_area(self, area_id: str, *, entry_point: bool = True) -> None:
        """Find results for an area."""
        if not (area_entry := self._async_resolve_up_area(area_id)):
            return

        if entry_point:
            # Add labels of this area
            self._add(ItemType.LABEL, area_entry.labels)

        # Automations referencing this area
        self._add(
            ItemType.AUTOMATION, automation.automations_with_area(self.hass, area_id)
        )

        # Scripts referencing this area
        self._add(ItemType.SCRIPT, script.scripts_with_area(self.hass, area_id))

        # Entity in this area, will extend this with the entities of the devices in this area
        entity_entries = er.async_entries_for_area(self._entity_registry, area_id)

        # Devices in this area
        for device in dr.async_entries_for_area(self._device_registry, area_id):
            self._add(ItemType.DEVICE, device.id)

            # Config entries for devices in this area
            if device_entry := self._device_registry.async_get(device.id):
                self._add(ItemType.CONFIG_ENTRY, device_entry.config_entries)

            # Automations referencing this device
            self._add(
                ItemType.AUTOMATION,
                automation.automations_with_device(self.hass, device.id),
            )

            # Scripts referencing this device
            self._add(ItemType.SCRIPT, script.scripts_with_device(self.hass, device.id))

            # Entities of this device
            for entity_entry in er.async_entries_for_device(
                self._entity_registry, device.id
            ):
                # Skip the entity if it's in a different area
                if entity_entry.area_id is not None:
                    continue
                entity_entries.append(entity_entry)

        # Process entities in this area
        for entity_entry in entity_entries:
            self._add(ItemType.ENTITY, entity_entry.entity_id)

            # If this entity also exists as a resource, we add it.
            if entity_entry.domain in self.EXIST_AS_ENTITY:
                self._add(ItemType(entity_entry.domain), entity_entry.entity_id)

            # Automations referencing this entity
            self._add(
                ItemType.AUTOMATION,
                automation.automations_with_entity(self.hass, entity_entry.entity_id),
            )

            # Scripts referencing this entity
            self._add(
                ItemType.SCRIPT,
                script.scripts_with_entity(self.hass, entity_entry.entity_id),
            )

            # Groups that have this entity as a member
            self._add(
                ItemType.GROUP,
                group.groups_with_entity(self.hass, entity_entry.entity_id),
            )

            # Persons that use this entity
            self._add(
                ItemType.PERSON,
                person.persons_with_entity(self.hass, entity_entry.entity_id),
            )

            # Scenes that reference this entity
            self._add(
                ItemType.SCENE,
                scene.scenes_with_entity(self.hass, entity_entry.entity_id),
            )

            # Config entries for entities in this area
            self._add(ItemType.CONFIG_ENTRY, entity_entry.config_entry_id)