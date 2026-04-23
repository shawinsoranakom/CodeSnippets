def _validate_device_maps(
    all_names, all_device_counts, all_device_maps, all_devices, is_static_group=True
):
    for node in all_names:
        devices = all_devices[node]
        if len(set(devices)) != len(devices):
            raise ValueError(f"Node {node} has duplicated devices\ndevices = {devices}")
        if not _tensorpipe_validate_devices(devices, all_device_counts[node]):
            raise ValueError(
                f"Node {node} has devices with invalid indices\n"
                f"devices = {devices}\n"
                f"device count = {all_device_counts[node]}"
            )

    for source_node in all_names:
        # For dynamic group (non-static) do not check the target node name since it may not have joined yet
        if is_static_group and not set(all_device_maps[source_node].keys()).issubset(
            all_names
        ):
            raise ValueError(
                f"Node {source_node} has invalid target node names in its device maps\n"
                f"device maps = {all_device_maps[source_node].keys()}\n"
                f"node names = {all_names}"
            )
        for target_node, map_ in all_device_maps[source_node].items():
            if len(set(map_.values())) != len(map_):
                raise ValueError(
                    f"Node {source_node} has duplicated target devices "
                    f"in its device map for {target_node}\n"
                    f"device map = {map_}"
                )
            if all_devices[source_node]:
                if not set(map_.keys()).issubset(all_devices[source_node]):
                    raise ValueError(
                        f"Node {source_node} has unexpected source devices "
                        f"in its device map for {target_node}\n"
                        f"device map = {map_}\n"
                        f"devices = {all_devices[source_node]}"
                    )
            elif not _tensorpipe_validate_devices(
                map_.keys(), all_device_counts[source_node]
            ):
                raise ValueError(
                    f"Node {source_node} has source devices with invalid indices "
                    f"in its device map for {target_node}\n"
                    f"device map = {map_}\n"
                    f"device count = {all_device_counts[source_node]}"
                )
            if all_devices.get(target_node, []):
                if not set(map_.values()).issubset(all_devices[target_node]):
                    raise ValueError(
                        f"Node {source_node} has unexpected target devices "
                        f"in its device map for {target_node}\n"
                        f"device map = {map_}\n"
                        f"devices = {all_devices[target_node]}"
                    )
            elif target_node in all_device_counts and not _tensorpipe_validate_devices(
                map_.values(), all_device_counts[target_node]
            ):
                raise ValueError(
                    f"Node {source_node} has target devices with invalid indices "
                    f"in its device map for {target_node}\n"
                    f"device map = {map_}\n"
                    f"device count = {all_device_counts[target_node]}"
                )