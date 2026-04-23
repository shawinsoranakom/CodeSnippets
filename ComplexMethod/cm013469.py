def get_comm_latency_between(
    parent_partition: Partition,
    child_partition: Partition,
    transfer_rate_bytes_per_sec: float,
) -> float:
    """Given two partitions (parent and child),
    calculate the communication latency between the two.
    """
    # If two partitions are on the same device, the comm latency is 0.
    if (
        parent_partition.logical_device_ids != []
        and child_partition.logical_device_ids != []
        and parent_partition.logical_device_ids == child_partition.logical_device_ids
    ):
        return 0.0
    # Keep tracking the communication size between parent and child
    comm_size = 0
    # Keep tracking all the counted node
    visited_nodes = set()
    # Go through all nodes in the child partition
    # If a node has input nodes from the parent partition,
    # the output size of those input nodes will be counted
    # and added to comm_size
    for node in child_partition.nodes:
        input_nodes: dict[Node, None] = {}
        map_arg(node.args, input_nodes.setdefault)
        map_arg(node.kwargs, input_nodes.setdefault)
        for n in input_nodes:
            if n in parent_partition.nodes and n not in visited_nodes:
                size_bytes = getattr(n, "size_bytes", None)
                if size_bytes is not None:
                    comm_size += size_bytes.output_size
                visited_nodes.add(n)
    return comm_size / transfer_rate_bytes_per_sec