def set_parents_and_children(partitions: list[Partition]) -> None:
    """Given a list of partitions, mark parents and children for each partition"""
    # Go through all nodes in a partition.
    # If a node's user is in other partition,
    # then the other partition is this partition's children.
    # This partition is the other partition's parent
    for partition in partitions:
        partition.children = set()
        partition.parents = set()
    for partition in partitions:
        for node in partition.nodes:
            # For each node in the current partition, find its users
            users = node.users
            for n in users:
                # Find which the partition the user node belongs to.
                # Note that if the node itself is also belongs to that partition,
                # that partition is not the child of the current partition
                for p in partitions:
                    if p != partition and n in p.nodes and node not in p.nodes:
                        partition.children.add(p)
                        p.parents.add(partition)
    return