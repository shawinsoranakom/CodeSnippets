def _check_for_zwave_cat(
    isy_data: IsyData, node: Group | Node, single_platform: Platform | None = None
) -> bool:
    """Check if the node matches the ISY Z-Wave Category for any platforms.

    This is for (presumably) every version of the ISY firmware, but only
    works for Z-Wave Devices with the devtype.cat property.
    """
    if node.protocol != PROTO_ZWAVE:
        return False

    if not hasattr(node, "zwave_props") or node.zwave_props is None:
        # Node doesn't have a device type category (non-Z-Wave device)
        return False

    device_type = node.zwave_props.category
    platforms = NODE_PLATFORMS if not single_platform else [single_platform]
    for platform in platforms:
        if any(
            device_type.startswith(t)
            for t in set(NODE_FILTERS[platform][FILTER_ZWAVE_CAT])
        ):
            isy_data.nodes[platform].append(node)
            return True

    return False