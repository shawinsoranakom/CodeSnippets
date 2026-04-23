def sort_placement_group_by_node_ip(placement_group: "PlacementGroup", master_addr: str = None) -> list[int]:
    r"""Sort the placement group bundles by their node IP addresses."""

    @ray.remote
    def _get_node_ip():
        return ray.util.get_node_ip_address().strip("[]")

    tasks = []
    for bundle_idx in range(placement_group.bundle_count):
        task = _get_node_ip.options(
            scheduling_strategy=PlacementGroupSchedulingStrategy(
                placement_group=placement_group,
                placement_group_bundle_index=bundle_idx,
            ),
        ).remote()
        tasks.append(task)

    bundle_ips = ray.get(tasks)
    bundle_node_ip_list = list(enumerate(bundle_ips))

    sorted_bundle_node_ip_list = sorted(bundle_node_ip_list, key=lambda x: x[1])
    sorted_bundle_indices = [item[0] for item in sorted_bundle_node_ip_list]

    if master_addr is not None:
        preferred_indices = [idx for idx, ip in bundle_node_ip_list if ip == master_addr]
        if preferred_indices:
            remaining = [i for i in sorted_bundle_indices if i not in preferred_indices]
            sorted_bundle_indices = preferred_indices + remaining

    return sorted_bundle_indices