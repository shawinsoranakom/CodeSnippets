def _async_search_script(
        self, script_entity_id: str, *, entry_point: bool = True
    ) -> None:
        """Find results for a script."""
        # Up resolve the script entity itself
        entity_entry = self._async_resolve_up_entity(script_entity_id)

        if entity_entry and entry_point:
            # Add labels of this script entity
            self._add(ItemType.LABEL, entity_entry.labels)

        # Find the blueprint used in this script
        self._add(
            ItemType.SCRIPT_BLUEPRINT,
            script.blueprint_in_script(self.hass, script_entity_id),
        )

        # Floors referenced in this script
        self._add(ItemType.FLOOR, script.floors_in_script(self.hass, script_entity_id))

        # Areas referenced in this script
        for area in script.areas_in_script(self.hass, script_entity_id):
            self._add(ItemType.AREA, area)
            self._async_resolve_up_area(area)

        # Devices referenced in this script
        for device in script.devices_in_script(self.hass, script_entity_id):
            self._add(ItemType.DEVICE, device)
            self._async_resolve_up_device(device)

        # Entities referenced in this script
        for entity_id in script.entities_in_script(self.hass, script_entity_id):
            self._add(ItemType.ENTITY, entity_id)
            self._async_resolve_up_entity(entity_id)

            # If this entity also exists as a resource, we add it.
            domain = split_entity_id(entity_id)[0]
            if domain in self.EXIST_AS_ENTITY:
                self._add(ItemType(domain), entity_id)

            # For an script, we want to unwrap the groups, to ensure we
            # relate this script to all those members as well.
            if domain == "group":
                for group_entity_id in group.get_entity_ids(self.hass, entity_id):
                    self._add(ItemType.ENTITY, group_entity_id)
                    self._async_resolve_up_entity(group_entity_id)

            # For an script, we want to unwrap the scenes, to ensure we
            # relate this script to all referenced entities as well.
            if domain == "scene":
                for scene_entity_id in scene.entities_in_scene(self.hass, entity_id):
                    self._add(ItemType.ENTITY, scene_entity_id)
                    self._async_resolve_up_entity(scene_entity_id)

            # Fully search the script if it is nested.
            # This makes the script return all results of the embedded script.
            if domain == "script":
                self._async_search_script(entity_id, entry_point=False)