def _check_for_insteon_type(
    isy_data: IsyData, node: Group | Node, single_platform: Platform | None = None
) -> bool:
    """Check if the node matches the Insteon type for any platforms.

    This is for (presumably) every version of the ISY firmware, but only
    works for Insteon device. "Node Server" (v5+) and Z-Wave and others will
    not have a type.
    """
    if node.protocol != PROTO_INSTEON:
        return False
    if not hasattr(node, "type") or node.type is None:
        # Node doesn't have a type (non-Insteon device most likely)
        return False

    device_type = node.type
    platforms = NODE_PLATFORMS if not single_platform else [single_platform]
    for platform in platforms:
        if any(
            device_type.startswith(t)
            for t in set(NODE_FILTERS[platform][FILTER_INSTEON_TYPE])
        ):
            # Hacky special-cases for certain devices with different platforms
            # included as subnodes. Note that special-cases are not necessary
            # on ISY 5.x firmware as it uses the superior NodeDefs method
            subnode_id = int(node.address.split(" ")[-1], 16)

            # FanLinc, which has a light module as one of its nodes.
            if platform == Platform.FAN and subnode_id == SUBNODE_FANLINC_LIGHT:
                isy_data.nodes[Platform.LIGHT].append(node)
                return True

            # Thermostats, which has a "Heat" and "Cool" sub-node on address 2 and 3
            if platform == Platform.CLIMATE and subnode_id in (
                SUBNODE_CLIMATE_COOL,
                SUBNODE_CLIMATE_HEAT,
            ):
                isy_data.nodes[Platform.BINARY_SENSOR].append(node)
                return True

            # IOLincs which have a sensor and relay on 2 different nodes
            if (
                platform == Platform.BINARY_SENSOR
                and device_type.startswith(TYPE_CATEGORY_SENSOR_ACTUATORS)
                and subnode_id == SUBNODE_IOLINC_RELAY
            ):
                isy_data.nodes[Platform.SWITCH].append(node)
                return True

            # Smartenit EZIO2X4
            if (
                platform == Platform.SWITCH
                and device_type.startswith(TYPE_EZIO2X4)
                and subnode_id in SUBNODE_EZIO2X4_SENSORS
            ):
                isy_data.nodes[Platform.BINARY_SENSOR].append(node)
                return True

            isy_data.nodes[platform].append(node)
            return True

    return False