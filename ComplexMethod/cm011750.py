def graph_partition(
        self,
    ) -> tuple[list[PartitionType], list[GraphPartitionSignature]]:
        """
        Given a list of BaseSchedulerNodes, split into a list of
        graph partitions and compute partition input/output signatures.
        """
        partitions: list[PartitionType] = []
        skip_cudagraph = True
        cur_partition: PartitionType = []
        skip_cudagraphs = []
        for node in self.nodes:
            node_should_partition = self.should_partition(node) is not None
            if cur_partition and skip_cudagraph != node_should_partition:
                partitions.append(cur_partition)
                skip_cudagraphs.append(skip_cudagraph)
                cur_partition = []

            skip_cudagraph = node_should_partition
            cur_partition.append(node)

        if cur_partition:
            partitions.append(cur_partition)
            skip_cudagraphs.append(skip_cudagraph)

        # Apply minimum partition size threshold: if a cudagraph-eligible partition
        # has fewer kernels than the threshold, mark it as non-cudagraphable
        min_size = config.triton.cudagraph_min_partition_size
        if min_size > 0:
            for i, (partition, skip) in enumerate(zip(partitions, skip_cudagraphs)):
                if not skip:
                    # Count kernels excluding NopKernelSchedulerNode
                    kernel_count = sum(
                        1
                        for n in partition
                        if not isinstance(n, NopKernelSchedulerNode)
                    )
                    if kernel_count < min_size:
                        skip_cudagraphs[i] = True
                        cudagraphs_log.debug(
                            "Partition %d has %d kernels, below minimum size %d, skipping cudagraph",
                            i,
                            kernel_count,
                            min_size,
                        )

        signatures = self.get_graph_partition_signature(
            partitions=partitions, skip_cudagraphs=skip_cudagraphs
        )
        self.compute_graph_partition_maps(signatures)

        self._log_graph_partitions(partitions, signatures)

        return partitions, signatures