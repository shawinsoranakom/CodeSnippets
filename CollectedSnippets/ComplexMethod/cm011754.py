def _codegen_partitions(self) -> None:
        """
        Split nodes into partitions and codegen each partition into separate functions.
        This allows further applying different optimizations (e.g., cudagraph) to
        each function.
        """
        partitions, signatures = self.graph_partition()

        if len(partitions) > 1:
            counters["inductor"]["cudagraph_partitions"] += len(partitions)

        with self.use_default_device_context(partitions, signatures):
            for partition, signature in zip(partitions, signatures):
                assert len(partition) >= 1, (
                    f"Each partition must have at least one node but found {len(partition)}"
                )

                if signature.skip_cudagraph:
                    self._codegen(partition)
                else:
                    self._codegen_partition_wrapper(partition, signature)

        num_partitions = next(self._graph_partition_counter)
        V.graph.wrapper_code.set_all_partition_names(num_partitions)

        # See [Note: Graph Partition Map for CUDAGraph]
        if num_partitions > 0:
            assert V.graph.partition_maps is not None
            assert num_partitions == len(V.graph.partition_maps), (
                f"Expect {num_partitions} partition maps but got {len(V.graph.partition_maps)}"
            )