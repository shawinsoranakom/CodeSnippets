def _default_group_nodes_for_combo_kernels(
        scheduler: Scheduler,
    ) -> list[list[BaseSchedulerNode]]:
        """
        Returns a list of lists of nodes that are to be grouped together.
        """
        sorted_nodes = scheduler._topological_sort_nodes()
        grouped_nodes = []
        max_num_nodes = config.combo_kernel_max_num_nodes

        excluded_buffer_names: OrderedSet[str] = OrderedSet(
            [
                buf_name
                for group in sorted_nodes
                for node in group
                if isinstance(node, FusedMixOrderReductions)
                for buf_name in node.get_buffer_names()
            ]
        )
        for nodes in sorted_nodes:
            # Group nodes by device first to avoid mixed-device fusion
            device_groups: dict[torch.device | None, list[BaseSchedulerNode]] = (
                defaultdict(list)
            )
            for node in nodes:
                device = node.get_device()
                if device and (device.type == "mps" or device.type == "cpu"):
                    continue

                # exclude nodes that read from FusedMixOrderReductions output buffers'
                if node.used_buffer_names() & excluded_buffer_names:
                    continue
                device_groups[device].append(node)

            # Sub-group by stream to avoid mixing nodes across stream
            # boundaries.  When multi-stream scheduling is inactive every
            # node maps to DEFAULT_STREAM_IDX so this is a no-op.
            for device_nodes in device_groups.values():
                stream_groups: dict[int, list[BaseSchedulerNode]] = defaultdict(list)
                for node in device_nodes:
                    stream_groups[scheduler.node_to_stream.get(node, 0)].append(node)
                for stream_nodes in stream_groups.values():
                    grouped_nodes.extend(
                        [
                            stream_nodes[i : i + max_num_nodes]
                            for i in range(0, len(stream_nodes), max_num_nodes)
                        ]
                    )
        return grouped_nodes