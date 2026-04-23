def _base_horizontal_partition(
        subkernel_nodes: list[BaseSchedulerNode],
        triton_scheduling: SIMDScheduling,
        node_info_map: dict[BaseSchedulerNode, NodeInfo],
        custom_algorithm: bool,
    ) -> list[list[BaseSchedulerNode]]:
        """Generates a list of lists of node info tuples which consist of (fused_nodes, tiling, numel, rnumel)
        for each subkernel node where each sublist is guaranteed to not exceed CUDA limits for number of args
        (read/writes) and to have the same 2D or 1D blocking strategy."""
        # TODO support combination of kernels with different block dimensions
        assert len(subkernel_nodes) >= 1
        mixed_sizes = config.combo_kernel_allow_mixed_sizes > 1 or (
            config.combo_kernel_allow_mixed_sizes == 1 and custom_algorithm
        )

        ndim_to_partition_state: dict[int, PartitionState] = defaultdict(
            lambda: PartitionState([], [], 0)
        )
        yelem_to_partition_state: dict[int, PartitionState] = defaultdict(
            lambda: PartitionState([], [], 0)
        )
        all_partitions = []

        for node in subkernel_nodes:
            tiled_groups = node_info_map[node].tiling
            node_info = node

            read_writes = node.read_writes
            read_write_count = len(read_writes.reads) + len(read_writes.writes)

            ndim = len(tiled_groups)
            assert ndim >= 2, f"Combokernel not support tile {tiled_groups}"

            # Skip 2d reductions (r0_,r1_) and 3D pointwise (x,y,z) from combo
            keys = tiled_groups.keys()
            if ("r0_" in keys and "r1_" in keys) or "z" in keys:
                all_partitions.append([node_info])
                continue

            if not mixed_sizes and ndim == 3:
                y_elem = tiled_groups["y"]
                partition_state = yelem_to_partition_state[y_elem]
                ComboKernel._update_partition(
                    partition_state, read_write_count, node_info
                )
            else:
                assert mixed_sizes or ndim <= 3, f"No mixed sizes: tile {tiled_groups}"
                partition_state = ndim_to_partition_state[ndim]
                ComboKernel._update_partition(
                    partition_state, read_write_count, node_info
                )

        for partition_state in ndim_to_partition_state.values():
            partition_state.finalize()
            all_partitions.extend(partition_state.partitions)
        for partition_state in yelem_to_partition_state.values():
            partition_state.finalize()
            all_partitions.extend(partition_state.partitions)
        return all_partitions