def partition_graph(
        self,
        fx_module: GraphModule,
        torch_module: torch.nn.Module,
        partitioner_config: PartitionerConfig,
    ) -> PartitionResult:
        """Given the fx module, torch module and partitioner_config,
        find the partitions, do the partitions,
        and then return a DAG and a new fx module with submodule nodes (partitions)
        """
        self.graph_module = fx_module
        self.torch_module = torch_module
        self.devices = partitioner_config.devices
        if len(self.devices) == 0:
            raise RuntimeError("No devices")
        # Tag the size in bytes to all nodes in the graph_module.
        get_size_of_all_nodes(self.graph_module)
        # Check if there are op nodes in the fx module
        nodes = self.graph_module.graph.nodes
        if all(node.op in {"placeholder", "get_attr", "output"} for node in nodes):
            raise RuntimeError("No Partition since no operations in the module")
        # Calculate total size of the fx module
        total_size_of_graph = 0
        for node in nodes:
            if node.op == "output":
                break
            total_size_of_graph += node.size_bytes.total_size
        # Find the device with the max mem size
        device_with_max_mem = max(self.devices, key=lambda d: d.available_mem_bytes)
        # AOT based partition
        if partitioner_config.mode == PartitionMode.aot_based:
            self.aot_based_partition(
                partitioner_config.node_to_partition_mapping,
                partitioner_config.partition_to_logical_device_mapping,
            )
        # Single partition if the whole module can be fit into one device
        elif total_size_of_graph <= device_with_max_mem.available_mem_bytes:
            self.find_single_partition(
                total_size_of_graph, logical_device_id=device_with_max_mem.logical_id
            )
        elif total_size_of_graph > sum(d.available_mem_bytes for d in self.devices):
            raise RuntimeError("Devices have no enough memory for the module")
        else:
            # Sparse nn based partition
            if partitioner_config.mode == PartitionMode.sparse_nn:
                available_mem_bytes = self.devices[0].available_mem_bytes
                if not all(
                    device.available_mem_bytes == available_mem_bytes
                    for device in self.devices
                ):
                    raise RuntimeError("All devices must have same memory size!")
                # sparse_nn_partition only support same memory size
                # TODO: add different size support for sparse_nn_partition
                self.sparse_nn_partition(available_mem_bytes)
            # Cost aware partition
            elif partitioner_config.mode == PartitionMode.cost_aware:
                self.cost_aware_partition(
                    partitioner_config.transfer_rate_bytes_per_sec,
                    partitioner_config.node_to_latency_mapping,
                )
            # KL based partition
            elif partitioner_config.mode == PartitionMode.kl_based:
                self.kl_based_partition(
                    partitioner_config.transfer_rate_bytes_per_sec,
                    partitioner_config.node_to_latency_mapping,
                )
            else:
                self.size_based_partition()

        # Saturate host if possible.
        if partitioner_config.saturate_host:
            self.saturate_host()

        # Partition the graph module based on the partition assignment.
        module_with_submodules = self.do_partition()

        # The DAG contains DAGNodes with info of each partition's input nodes, output nodes
        # and how partitions are connected.
        dag = self.dump_dag(module_with_submodules)
        ret = PartitionResult(dag, module_with_submodules)
        return ret