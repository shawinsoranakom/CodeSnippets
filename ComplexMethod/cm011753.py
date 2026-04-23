def update_graph_partition_default_device(
        self, partitions: list[PartitionType], signatures: list[GraphPartitionSignature]
    ) -> None:
        # Note: [Graph Partition Device Contexts]
        # Entering a device context takes 60 microseconds and exiting a device
        # context takes 20 microseconds. If all graph partitions and
        # cudagraph-unsafe ops happen on the same device, we can share the
        # device context.

        if len(partitions) == 1 and not signatures[0].skip_cudagraph:
            # If there is only 1 cudagraph partition, the device context
            # should happen within the cudagraph partition, which
            # would be removed by cudagraph.
            return

        def get_cudagraph_partition_device(partition: PartitionType) -> torch.device:
            partition_device = partition[0].get_device()
            assert partition_device is not None
            return partition_device

        def all_on_target_device(
            partition: PartitionType, target_device: torch.device
        ) -> bool:
            for node in partition:
                device = node.get_device()
                if device != target_device:
                    return False
            return True

        cudagraph_partition_device = None
        for partition, signature in zip(partitions, signatures):
            if not signature.skip_cudagraph:
                cudagraph_partition_device = get_cudagraph_partition_device(partition)
                break

        # all partitions skip cudagraph
        if cudagraph_partition_device is None:
            return

        for partition, signature in zip(partitions, signatures):
            if signature.skip_cudagraph and not all_on_target_device(
                partition, cudagraph_partition_device
            ):
                return

        self.default_device_context = cudagraph_partition_device