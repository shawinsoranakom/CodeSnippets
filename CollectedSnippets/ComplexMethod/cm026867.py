def _categorize_nodes(
    isy_data: IsyData, nodes: Nodes, ignore_identifier: str, sensor_identifier: str
) -> None:
    """Sort the nodes to their proper platforms."""
    for path, node in nodes:
        ignored = ignore_identifier in path or ignore_identifier in node.name
        if ignored:
            # Don't import this node as a device at all
            continue

        if hasattr(node, "parent_node") and node.parent_node is None:
            # This is a physical device / parent node
            isy_data.devices[node.address] = _generate_device_info(node)
            isy_data.root_nodes[Platform.BUTTON].append(node)
            # Any parent node can have communication errors:
            isy_data.aux_properties[Platform.SENSOR].append((node, PROP_COMMS_ERROR))
            # Add Ramp Rate and On Levels for Dimmable Load devices
            if getattr(node, "is_dimmable", False):
                aux_controls = ROOT_AUX_CONTROLS.intersection(node.aux_properties)
                for control in aux_controls:
                    platform = NODE_AUX_FILTERS[control]
                    isy_data.aux_properties[platform].append((node, control))
            if hasattr(node, TAG_ENABLED):
                isy_data.aux_properties[Platform.SWITCH].append((node, TAG_ENABLED))
            _add_backlight_if_supported(isy_data, node)

        if node.protocol == PROTO_GROUP:
            isy_data.nodes[ISY_GROUP_PLATFORM].append(node)
            continue

        if node.protocol == PROTO_INSTEON:
            for control in node.aux_properties:
                if control in SKIP_AUX_PROPS:
                    continue
                isy_data.aux_properties[Platform.SENSOR].append((node, control))

        if sensor_identifier in path or sensor_identifier in node.name:
            # User has specified to treat this as a sensor. First we need to
            # determine if it should be a binary_sensor.
            if _is_sensor_a_binary_sensor(isy_data, node):
                continue
            isy_data.nodes[Platform.SENSOR].append(node)
            continue

        # We have a bunch of different methods for determining the device type,
        # each of which works with different ISY firmware versions or device
        # family. The order here is important, from most reliable to least.
        if _check_for_node_def(isy_data, node):
            continue
        if _check_for_insteon_type(isy_data, node):
            continue
        if _check_for_zwave_cat(isy_data, node):
            continue
        if _check_for_uom_id(isy_data, node):
            continue
        if _check_for_states_in_uom(isy_data, node):
            continue

        # Fallback as as sensor, e.g. for un-sortable items like NodeServer nodes.
        isy_data.nodes[Platform.SENSOR].append(node)