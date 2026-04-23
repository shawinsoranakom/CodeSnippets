async def async_setup_entry(
    hass: HomeAssistant,
    entry: IsyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the ISY binary sensor platform."""
    entities: list[
        ISYInsteonBinarySensorEntity
        | ISYBinarySensorEntity
        | ISYBinarySensorHeartbeat
        | ISYBinarySensorProgramEntity
    ] = []
    entities_by_address: dict[
        str,
        ISYInsteonBinarySensorEntity
        | ISYBinarySensorEntity
        | ISYBinarySensorHeartbeat
        | ISYBinarySensorProgramEntity,
    ] = {}
    child_nodes: list[
        tuple[Node, BinarySensorDeviceClass | None, str | None, DeviceInfo | None]
    ] = []
    entity: (
        ISYInsteonBinarySensorEntity
        | ISYBinarySensorEntity
        | ISYBinarySensorHeartbeat
        | ISYBinarySensorProgramEntity
    )

    isy_data = entry.runtime_data
    devices = isy_data.devices
    for node in isy_data.nodes[Platform.BINARY_SENSOR]:
        assert isinstance(node, Node)
        device_info = devices.get(node.primary_node)
        device_class, device_type = _detect_device_type_and_class(node)
        if node.protocol == PROTO_INSTEON:
            if node.parent_node is not None:
                # We'll process the Insteon child nodes last, to ensure all parent
                # nodes have been processed
                child_nodes.append((node, device_class, device_type, device_info))
                continue
            entity = ISYInsteonBinarySensorEntity(
                node, device_class, device_info=device_info
            )
        else:
            entity = ISYBinarySensorEntity(node, device_class, device_info=device_info)
        entities.append(entity)
        entities_by_address[node.address] = entity

    # Handle some special child node cases for Insteon Devices
    for node, device_class, device_type, device_info in child_nodes:
        subnode_id = int(node.address.split(" ")[-1], 16)
        # Handle Insteon Thermostats
        if device_type is not None and device_type.startswith(TYPE_CATEGORY_CLIMATE):
            if subnode_id == SUBNODE_CLIMATE_COOL:
                # Subnode 2 is the "Cool Control" sensor
                # It never reports its state until first use is
                # detected after an ISY Restart, so we assume it's off.
                # As soon as the ISY Event Stream connects if it has a
                # valid state, it will be set.
                entity = ISYInsteonBinarySensorEntity(
                    node, BinarySensorDeviceClass.COLD, False, device_info=device_info
                )
                entities.append(entity)
            elif subnode_id == SUBNODE_CLIMATE_HEAT:
                # Subnode 3 is the "Heat Control" sensor
                entity = ISYInsteonBinarySensorEntity(
                    node, BinarySensorDeviceClass.HEAT, False, device_info=device_info
                )
                entities.append(entity)
            continue

        if device_class in DEVICE_PARENT_REQUIRED:
            parent_entity = entities_by_address.get(node.parent_node.address)
            if not parent_entity:
                _LOGGER.error(
                    (
                        "Node %s has a parent node %s, but no device "
                        "was created for the parent. Skipping"
                    ),
                    node.address,
                    node.parent_node,
                )
                continue

        if device_class in (
            BinarySensorDeviceClass.OPENING,
            BinarySensorDeviceClass.MOISTURE,
        ):
            # These sensors use an optional "negative" subnode 2 to
            # snag all state changes
            if subnode_id == SUBNODE_NEGATIVE:
                assert isinstance(parent_entity, ISYInsteonBinarySensorEntity)
                parent_entity.add_negative_node(node)
            elif subnode_id == SUBNODE_HEARTBEAT:
                assert isinstance(parent_entity, ISYInsteonBinarySensorEntity)
                # Subnode 4 is the heartbeat node, which we will
                # represent as a separate binary_sensor
                entity = ISYBinarySensorHeartbeat(
                    node, parent_entity, device_info=device_info
                )
                parent_entity.add_heartbeat_device(entity)
                entities.append(entity)
            continue
        if (
            device_class == BinarySensorDeviceClass.MOTION
            and device_type is not None
            and any(device_type.startswith(t) for t in TYPE_INSTEON_MOTION)
        ):
            # Special cases for Insteon Motion Sensors I & II:
            # Some subnodes never report status until activated, so
            # the initial state is forced "OFF"/"NORMAL" if the
            # parent device has a valid state. This is corrected
            # upon connection to the ISY event stream if subnode has a valid state.
            assert isinstance(parent_entity, ISYInsteonBinarySensorEntity)
            initial_state = None if parent_entity.state is None else False
            if subnode_id == SUBNODE_DUSK_DAWN:
                # Subnode 2 is the Dusk/Dawn sensor
                entity = ISYInsteonBinarySensorEntity(
                    node, BinarySensorDeviceClass.LIGHT, device_info=device_info
                )
                entities.append(entity)
                continue
            if subnode_id == SUBNODE_LOW_BATTERY:
                # Subnode 3 is the low battery node
                entity = ISYInsteonBinarySensorEntity(
                    node,
                    BinarySensorDeviceClass.BATTERY,
                    initial_state,
                    device_info=device_info,
                )
                entities.append(entity)
                continue
            if subnode_id in SUBNODE_TAMPER:
                # Tamper Sub-node for MS II. Sometimes reported as "A" sometimes
                # reported as "10", which translate from Hex to 10 and 16 resp.
                entity = ISYInsteonBinarySensorEntity(
                    node,
                    BinarySensorDeviceClass.PROBLEM,
                    initial_state,
                    device_info=device_info,
                )
                entities.append(entity)
                continue
            if subnode_id in SUBNODE_MOTION_DISABLED:
                # Motion Disabled Sub-node for MS II ("D" or "13")
                entity = ISYInsteonBinarySensorEntity(node, device_info=device_info)
                entities.append(entity)
                continue

        # We don't yet have any special logic for other sensor
        # types, so add the nodes as individual devices
        entity = ISYBinarySensorEntity(
            node, force_device_class=device_class, device_info=device_info
        )
        entities.append(entity)

    for name, status, _ in isy_data.programs[Platform.BINARY_SENSOR]:
        entities.append(ISYBinarySensorProgramEntity(name, status))

    async_add_entities(entities)