def _get_autobind_cpu_ids(
        self, cpu_selector: Callable[[list[LogicalCPUInfo]], list[LogicalCPUInfo]]
    ) -> tuple[list[list[LogicalCPUInfo]], list[LogicalCPUInfo]]:
        """
        Return CPU ids to bind based on NUMA nodes, and CPU ids reserved for
        other processes.
        Currently for rank N, only CPU ids on the N-th node in available NUMA
        node list will be selected.
        Args:
            cpu_selector: a callable object to select CPUs from a CPU list
            of a physical core. The input is a LogicalCPUInfo list contains
            logical CPUs of a physical CPU, sorted by the LogicalCPUInfo.id.
            A selected LogicalCPUInfo list should be returned.
        """

        # this memory node list has been sliced for DP offset
        allowed_numa_nodes = cr_utils.get_visible_memory_node()
        logical_cpu_list = cr_utils.get_allowed_cpu_list()

        local_world_size = self.local_world_size
        assert (
            len(allowed_numa_nodes) >= local_world_size or self.simulate_multi_node
        ), (
            f"Not enough allowed NUMA nodes to bind threads of "
            f"{local_world_size} local CPUWorkers. "
            f"Allowed NUMA nodes are {allowed_numa_nodes}. "
            "Please try to bind threads manually or decrease DP/TP/PP."
        )

        # Generate OMP CPU list for each rank
        cpu_lists_of_ranks = []
        reserved_cpu_list = []
        total_cpu_num = 0
        for local_rank in range(self.local_world_size):
            if not self.simulate_multi_node:
                selected_numa_node = allowed_numa_nodes[local_rank]
                selected_logical_cpu_list = [
                    x for x in logical_cpu_list if x.numa_node == selected_numa_node
                ]
            else:
                world_size_across_dp = self.local_world_size * self.internal_dp_size
                assert len(logical_cpu_list) >= world_size_across_dp
                selected_logical_cpu_list = sorted(
                    logical_cpu_list, key=lambda x: x.numa_node
                )
                sim_cpu_num_per_node = (
                    len(selected_logical_cpu_list) // world_size_across_dp
                )
                assert self.local_dp_rank is not None
                start_idx = (
                    local_rank + self.local_world_size * self.local_dp_rank
                ) * sim_cpu_num_per_node
                selected_logical_cpu_list = selected_logical_cpu_list[
                    start_idx : (start_idx + sim_cpu_num_per_node)
                ]

            # Select logical CPUs on same physical cores via cpu_selector
            core_to_cpus: dict[int, list[LogicalCPUInfo]] = {}
            for cpu_info in selected_logical_cpu_list:
                if cpu_info.physical_core not in core_to_cpus:
                    core_to_cpus[cpu_info.physical_core] = []
                core_to_cpus[cpu_info.physical_core].append(cpu_info)
            selected_logical_cpu_list = []
            for cpu_list in core_to_cpus.values():
                cpu_list = sorted(cpu_list, key=lambda x: x.id)
                selected_logical_cpu_list.extend(cpu_selector(cpu_list))

            # sort selected cores based on core id
            selected_logical_cpu_list = sorted(
                selected_logical_cpu_list, key=lambda x: x.id
            )

            cpu_lists_of_ranks.append(selected_logical_cpu_list)
            total_cpu_num += len(selected_logical_cpu_list)

        # Reserve CPUs for other processes
        if total_cpu_num <= self.reserve_cpu_num:
            logger.warning(
                "Selected CPU core number (%s) "
                "should be greater than reserved CPU core "
                "number (%s).",
                total_cpu_num,
                self.reserve_cpu_num,
            )
            return cpu_lists_of_ranks, []

        reserve_num_per_rank = [
            self.reserve_cpu_num // self.local_world_size
        ] * self.local_world_size
        # last rank first
        for i in range(
            self.local_world_size - 1,
            self.local_world_size - 1 - self.reserve_cpu_num % self.local_world_size,
            -1,
        ):
            reserve_num_per_rank[i] += 1
        for i in range(self.local_world_size):
            num = reserve_num_per_rank[i]
            if num > 0:
                reserved_cpu_list.extend(cpu_lists_of_ranks[i][-num:])
                cpu_lists_of_ranks[i] = cpu_lists_of_ranks[i][:-num]

        return cpu_lists_of_ranks, reserved_cpu_list