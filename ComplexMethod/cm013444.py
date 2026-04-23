def size_based_partition(self) -> None:
        """This method is to partition the fx module based on memory size.
        It uses greedy approach. The result may not be the best.
        The basic idea is:
        Step 1:
        Find a device which has enough memory to fit the current node, create a empty partition
        with the size of that device.
        Then keep adding the following nodes into the partition until the partition is full.
        Step 2:
        Repeat Step 1 until no device left
        Step 3:
        If some nodes are left, create a partition for each left node (single node partition).
        and then try to map those partitions into logical devices with enough mem left.
        """

        def find_device_based_on_size(node: Node) -> Device:
            """Given a node, this function is to find a logical device
            that could fit the node.
            """
            mem_size_needed = get_extra_size_of(node, set())
            device = Device("", -1, -1)
            for d in self.devices:
                if (
                    d not in occupied_devices
                    and d.available_mem_bytes >= mem_size_needed
                ):
                    device = d
                    break
            if device.available_mem_bytes < 0:
                raise RuntimeError(str(node) + "is too large to fit any device")
            occupied_devices.append(device)
            return device

        # Track partition and its left mem size
        partition_to_left_mem_bytes: dict[Partition, int] = {}
        # Track all the devices that have been used
        occupied_devices: list[Device] = []
        partition = self.create_partition()
        for node in self.graph_module.graph.nodes:
            if node.op in {"call_module", "call_method", "call_function"}:
                # Check if there are devices left
                if len(self.partitions) <= len(self.devices):
                    total_size_of_input_nodes = get_extra_size_of(node, partition.nodes)
                    # Check if the current partition is the very first partition
                    if partition.used_mem_bytes == 0:
                        # Find a device to fit the first node, return available mem size
                        device = find_device_based_on_size(node)
                        occupied_devices.append(device)
                        # Update partition and its left mem size
                        partition_to_left_mem_bytes[partition] = (
                            device.available_mem_bytes
                        )
                        # Update available mem for the current partition
                        partition.logical_device_ids.append(device.logical_id)
                    else:
                        # The current partition is not the first partition
                        # Check if the current node can fit into current partition
                        if (
                            partition_to_left_mem_bytes[partition]
                            < total_size_of_input_nodes
                        ):
                            # Check if no device is left
                            if len(self.partitions) == len(self.devices):
                                # No device is left
                                # Create the first single node partition for the current node
                                self.create_single_node_partition(node)
                                continue
                            # Some devices are still left
                            # Create a new partition with a mem size that is enough for the current node
                            device = find_device_based_on_size(node)
                            partition = self.create_partition()
                            total_size_of_input_nodes = get_extra_size_of(
                                node, partition.nodes
                            )
                            partition_to_left_mem_bytes[partition] = (
                                device.available_mem_bytes
                            )
                            partition.logical_device_ids.append(device.logical_id)
                    partition.add_node(node)
                    partition_to_left_mem_bytes[partition] -= total_size_of_input_nodes
                # Create single node partitions if no device is left
                else:
                    self.create_single_node_partition(node)
        reorganize_partitions(self.partitions)
        # Get the node to partition mapping
        self.node_to_partition = get_node_to_partition_mapping(self.partitions)
        # Mapping all partitions into device
        found_partition_to_device_mapping = get_device_to_partitions_mapping(
            self.partitions, self.devices
        )
        if not found_partition_to_device_mapping:
            raise RuntimeError("Cannot Get a Valid Partition to Logical Device Mapping")
        return