def _log_graph_partitions(
        self,
        partitions: list[PartitionType],
        signatures: list[GraphPartitionSignature],
    ) -> None:
        if not cudagraphs_log.isEnabledFor(logging.DEBUG):
            return

        # Don't log partition reasons for CPU-only graphs since cudagraph
        # partitioning is not relevant when there are no GPU devices
        has_gpu_device = any(is_gpu(device) for device in V.graph.device_types)
        if not has_gpu_device:
            return

        cudagraphable_count = sum(1 for s in signatures if not s.skip_cudagraph)
        non_cudagraphable_count = len(signatures) - cudagraphable_count
        cudagraphs_log.debug(
            "Created %d graph partitions: %d cudagraphable, %d non-cudagraphable",
            len(partitions),
            cudagraphable_count,
            non_cudagraphable_count,
        )
        for i, (partition, signature) in enumerate(zip(partitions, signatures)):
            cudagraphs_log.debug(
                "  Partition %d: %d nodes, %s, inputs=%d, outputs=%d",
                i,
                len(partition),
                "non-cudagraphable" if signature.skip_cudagraph else "cudagraphable",
                len(signature.input_nodes),
                len(signature.output_nodes),
            )
            if signature.skip_cudagraph:
                # Log details for each non-cudagraphable node
                for node in partition:
                    self._log_non_cudagraphable_node(node)