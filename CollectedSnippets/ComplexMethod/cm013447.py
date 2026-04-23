def kl_based_partition(
        self,
        transfer_rate_bytes_per_sec: float,
        node_to_latency_mapping: dict[Node, NodeLatency],
    ) -> None:
        """This function is a cost aware partition based
        on Kernighan-Lin algorithm.
        First, the graph is partitioned using size_based_partition.
        Then, each node is swapped with any other node in a different
        partition, and at the same time, the cost is estimated after
        the swapping.
        For example, we have nodes n0, n1, n2, n3 and n4.
        Using size_based_partition, n0 and n1 are in Partition p0.
        n2, n3 and n4 in Partition p1. The current cost is estimated.
        We first tried using n0 to swap with n2 from the other partition.
        Then we see that swapping n0 and n2 shows a lower cost
        than the current cost and it is the minimum among other pairs like
        (n0, None)(This means moving n0 to Partition without swapping other nodes),
        (n0, n3) and (n0, n4). We swap n0 and n2 and set the new cost
        as the current cost.
        Then We repeat this process for all the other nodes until all swapping pairs
        are tried.
        """

        def swap_nodes(
            n0: Node | None, n1: Node | None, p0: Partition, p1: Partition
        ) -> None:
            # Either n0 or n1 could be None
            # That means we simply move the node
            # to another partition
            if n0 is not None:
                p0.remove_node(n0)
                p1.add_node(n0)
            if n1 is not None:
                p0.add_node(n1)
                p1.remove_node(n1)

        def try_swap_nodes(
            n0: Node | None,
            n1: Node | None,
            p0: Partition,
            p1: Partition,
            node_to_latency_mapping: dict[Node, NodeLatency],
            transfer_rate_per_sec: float,
        ) -> float:
            cost = float("inf")
            swap_nodes(n0, n1, p0, p1)
            # Reorganize partitions after swapping
            reorganize_partitions(self.partitions)
            # Check if there is a circular dependency after swapping
            if (not check_dependency(p0)) and (not check_dependency(p1)):
                reset_partition_device(self.partitions)
                partition_to_latency_mapping = get_partition_to_latency_mapping(
                    self.partitions, node_to_latency_mapping
                )
                # Check if all partitions can be mapped to logical devices after swapping
                found_device = get_device_to_partitions_mapping(
                    self.partitions, self.devices
                )
                if not found_device:
                    cost = float("inf")
                else:
                    cost = get_latency_of_partitioned_graph(
                        self.partitions,
                        partition_to_latency_mapping,
                        transfer_rate_bytes_per_sec,
                    )
            # Swap back and reset all partitions back to original
            swap_nodes(n1, n0, p0, p1)
            reorganize_partitions(self.partitions)
            reset_partition_device(self.partitions)
            get_device_to_partitions_mapping(self.partitions, self.devices)
            return cost

        def swap_node_to_partition(
            node: Node,
            p0: Partition,
            p1: Partition,
            node_to_latency_mapping: dict[Node, NodeLatency],
            transfer_rate_per_sec: float,
        ) -> tuple[float, list[Node]]:
            """This function helps to swap one node from partition p0
            with all the nodes in another partition p1
            """
            p1_nodes = list(p1.nodes) + [None]
            min_cost = float("inf")
            node_pair: list[Node] = []
            for n1 in p1_nodes:
                # Ignore the node if it is not a op node
                if n1 is not None and n1.op in {"placeholder", "get_attr"}:
                    continue
                # Try swapping node in p0 with n1 in p1
                cost = try_swap_nodes(
                    node, n1, p0, p1, node_to_latency_mapping, transfer_rate_per_sec
                )
                if cost < min_cost:
                    # pyrefly: ignore [bad-assignment]
                    node_pair = [node, n1]
                    min_cost = cost
            return cost, node_pair  # type: ignore[possibly-undefined]

        # First use size_base_partition
        self.size_based_partition()
        partition_to_latency_mapping = get_partition_to_latency_mapping(
            self.partitions, node_to_latency_mapping
        )
        # Calculate the cost of the partitions
        cost = get_latency_of_partitioned_graph(
            self.partitions, partition_to_latency_mapping, transfer_rate_bytes_per_sec
        )
        # Keep tracking the node pair that shows the better cost
        node_pair: list[Node] = []
        # Keep tracking the partition pair of node pair
        partition_pair: list[Partition] = []
        # Collect all the op nodes from the graph
        op_nodes = [
            n
            for n in self.graph_module.graph.nodes
            if n.op not in {"placeholder", "get_attr", "output"}
        ]
        for node in op_nodes:
            # Find which partition the current node belongs
            p0_index = self.node_to_partition[node]
            p0 = self.partitions[p0_index]
            # Go through all the other partitions to swap
            # with other nodes from those partitions
            for p1_index, _ in enumerate(self.partitions):
                if p0_index != p1_index:
                    p1 = self.partitions[p1_index]
                    new_cost, new_node_pair = swap_node_to_partition(
                        node,
                        p0,
                        p1,
                        node_to_latency_mapping,
                        transfer_rate_bytes_per_sec,
                    )
                    # Update the cost
                    # Track the swapped node pair and their partitions
                    if new_cost < cost:
                        cost = new_cost
                        node_pair = new_node_pair
                        partition_pair = [p0, p1]
            # Do the swapping after trying all the nodes from a partition
            if len(node_pair) != 0:
                swap_nodes(
                    node_pair[0], node_pair[1], partition_pair[0], partition_pair[1]
                )
                reorganize_partitions(self.partitions)
                get_device_to_partitions_mapping(self.partitions, self.devices)
        reorganize_partitions(self.partitions)
        # Mapping the device to the partition
        get_device_to_partitions_mapping(self.partitions, self.devices)
        return