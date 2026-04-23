def _async_add_new_entities() -> None:
        # Remove devices whose nodes have disappeared from the API.
        # The firmware removes deregistered RF/wired nodes automatically.
        # BSRH box sensors that are physically unplugged from the PCB are
        # not deregistered by the firmware and will never appear here as stale.
        stale_node_ids = known_nodes - coordinator.data.nodes.keys()
        if stale_node_ids:
            device_reg = dr.async_get(hass)
            mac = entry.unique_id
            for node_id in stale_node_ids:
                device = device_reg.async_get_device(
                    identifiers={(DOMAIN, f"{mac}_{node_id}")}
                )
                if device:
                    device_reg.async_update_device(
                        device.id,
                        remove_config_entry_id=entry.entry_id,
                    )
            known_nodes.difference_update(stale_node_ids)

        new_entities: list[SensorEntity] = []
        for node in coordinator.data.nodes.values():
            if node.node_id in known_nodes:
                continue
            known_nodes.add(node.node_id)
            new_entities.extend(
                DucoSensorEntity(coordinator, node, description)
                for description in SENSOR_DESCRIPTIONS
                if node.general.node_type in description.node_types
            )
            new_entities.extend(
                DucoBoxSensorEntity(coordinator, node, description)
                for description in BOX_SENSOR_DESCRIPTIONS
                if node.general.node_type == NodeType.BOX
            )
        if new_entities:
            async_add_entities(new_entities)