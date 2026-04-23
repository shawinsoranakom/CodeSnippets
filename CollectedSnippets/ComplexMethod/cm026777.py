def _async_search_automation(self, automation_entity_id: str) -> None:
        """Find results for an automation."""
        # Up resolve the automation entity itself
        if entity_entry := self._async_resolve_up_entity(automation_entity_id):
            # Add labels of this automation entity
            self._add(ItemType.LABEL, entity_entry.labels)

        # Find the blueprint used in this automation
        self._add(
            ItemType.AUTOMATION_BLUEPRINT,
            automation.blueprint_in_automation(self.hass, automation_entity_id),
        )

        # Floors referenced in this automation
        self._add(
            ItemType.FLOOR,
            automation.floors_in_automation(self.hass, automation_entity_id),
        )

        # Areas referenced in this automation
        for area in automation.areas_in_automation(self.hass, automation_entity_id):
            self._add(ItemType.AREA, area)
            self._async_resolve_up_area(area)

        # Devices referenced in this automation
        for device in automation.devices_in_automation(self.hass, automation_entity_id):
            self._add(ItemType.DEVICE, device)
            self._async_resolve_up_device(device)

        # Entities referenced in this automation
        for entity_id in automation.entities_in_automation(
            self.hass, automation_entity_id
        ):
            self._add(ItemType.ENTITY, entity_id)
            self._async_resolve_up_entity(entity_id)

            # If this entity also exists as a resource, we add it.
            domain = split_entity_id(entity_id)[0]
            if domain in self.EXIST_AS_ENTITY:
                self._add(ItemType(domain), entity_id)

            # For an automation, we want to unwrap the groups, to ensure we
            # relate this automation to all those members as well.
            if domain == "group":
                for group_entity_id in group.get_entity_ids(self.hass, entity_id):
                    self._add(ItemType.ENTITY, group_entity_id)
                    self._async_resolve_up_entity(group_entity_id)

            # For an automation, we want to unwrap the scenes, to ensure we
            # relate this automation to all referenced entities as well.
            if domain == "scene":
                for scene_entity_id in scene.entities_in_scene(self.hass, entity_id):
                    self._add(ItemType.ENTITY, scene_entity_id)
                    self._async_resolve_up_entity(scene_entity_id)

            # Fully search the script if it is part of an automation.
            # This makes the automation return all results of the embedded script.
            if domain == "script":
                self._async_search_script(entity_id, entry_point=False)