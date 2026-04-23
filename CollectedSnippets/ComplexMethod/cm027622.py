def async_extract_referenced_entity_ids(
    hass: HomeAssistant, target_selection: TargetSelection, expand_group: bool = True
) -> SelectedEntities:
    """Extract referenced entity IDs from a target selection."""
    selected = SelectedEntities()

    if not target_selection.has_any_target:
        return selected

    entity_ids: set[str] | list[str] = target_selection.entity_ids
    if expand_group:
        entity_ids = group.expand_entity_ids(hass, entity_ids)

    selected.referenced.update(entity_ids)

    if (
        not target_selection.device_ids
        and not target_selection.area_ids
        and not target_selection.floor_ids
        and not target_selection.label_ids
    ):
        return selected

    entities = er.async_get(hass).entities
    dev_reg = dr.async_get(hass)
    area_reg = ar.async_get(hass)

    if target_selection.floor_ids:
        floor_reg = fr.async_get(hass)
        for floor_id in target_selection.floor_ids:
            if floor_id not in floor_reg.floors:
                selected.missing_floors.add(floor_id)

    for area_id in target_selection.area_ids:
        if area_id not in area_reg.areas:
            selected.missing_areas.add(area_id)

    for device_id in target_selection.device_ids:
        if device_id not in dev_reg.devices:
            selected.missing_devices.add(device_id)

    if target_selection.label_ids:
        label_reg = lr.async_get(hass)
        for label_id in target_selection.label_ids:
            if label_id not in label_reg.labels:
                selected.missing_labels.add(label_id)

            for entity_entry in entities.get_entries_for_label(label_id):
                if entity_entry.hidden_by is None:
                    selected.indirectly_referenced.add(entity_entry.entity_id)

            for device_entry in dev_reg.devices.get_devices_for_label(label_id):
                selected.referenced_devices.add(device_entry.id)

            for area_entry in area_reg.areas.get_areas_for_label(label_id):
                selected.referenced_areas.add(area_entry.id)

    # Find areas for targeted floors
    if target_selection.floor_ids:
        selected.referenced_areas.update(
            area_entry.id
            for floor_id in target_selection.floor_ids
            for area_entry in area_reg.areas.get_areas_for_floor(floor_id)
        )

    selected.referenced_areas.update(target_selection.area_ids)
    selected.referenced_devices.update(target_selection.device_ids)

    if not selected.referenced_areas and not selected.referenced_devices:
        return selected

    # Add indirectly referenced by device
    selected.indirectly_referenced.update(
        entry.entity_id
        for device_id in selected.referenced_devices
        for entry in entities.get_entries_for_device_id(device_id)
        # Do not add entities which are hidden or which are config
        # or diagnostic entities.
        if (entry.entity_category is None and entry.hidden_by is None)
    )

    # Find devices for targeted areas
    referenced_devices_by_area: set[str] = set()
    if selected.referenced_areas:
        for area_id in selected.referenced_areas:
            referenced_devices_by_area.update(
                device_entry.id
                for device_entry in dev_reg.devices.get_devices_for_area_id(area_id)
            )
    selected.referenced_devices.update(referenced_devices_by_area)

    # Add indirectly referenced by area
    selected.indirectly_referenced.update(
        entry.entity_id
        for area_id in selected.referenced_areas
        # The entity's area matches a targeted area
        for entry in entities.get_entries_for_area_id(area_id)
        # Do not add entities which are hidden or which are config
        # or diagnostic entities.
        if entry.entity_category is None and entry.hidden_by is None
    )
    # Add indirectly referenced by area through device
    selected.indirectly_referenced.update(
        entry.entity_id
        for device_id in referenced_devices_by_area
        for entry in entities.get_entries_for_device_id(device_id)
        # Do not add entities which are hidden or which are config
        # or diagnostic entities.
        if (
            entry.entity_category is None
            and entry.hidden_by is None
            and (
                # The entity's device matches a device referenced
                # by an area and the entity
                # has no explicitly set area
                not entry.area_id
            )
        )
    )

    return selected