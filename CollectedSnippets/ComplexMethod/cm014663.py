def _add_mock_hardware(
        self,
        *,
        num_sockets: int,
        num_numa_nodes_per_socket: int,
        num_gpus_per_numa_node: int,
        num_l3_caches_per_numa_node: int,
        num_physical_core_per_l3_cache: int,
    ) -> None:
        """
        It's not fun, but we mock everything down to sysfs level
        to make sure we get really thorough coverage.
        """
        for socket_index in range(num_sockets):
            for numa_node_index in range(
                self._mock_num_numa_nodes,
                self._mock_num_numa_nodes + num_numa_nodes_per_socket,
            ):
                self._mock_file_contents(
                    file_path=f"/sys/devices/system/node/node{numa_node_index}/cpulist",
                    contents=f"{self._mock_num_logical_cpus}-"
                    + f"{self._mock_num_logical_cpus + num_l3_caches_per_numa_node * num_physical_core_per_l3_cache * 2 - 1}",
                )
                for gpu_index in range(
                    len(self._mock_device_properties),
                    len(self._mock_device_properties) + num_gpus_per_numa_node,
                ):
                    device_properties = MockDeviceProperties(
                        name=f"mock_gpu_{gpu_index}",
                        major=8,
                        minor=0,
                        total_memory="512GB",
                        multi_processor_count=256,
                        uuid=f"mock_gpu_uuid_{gpu_index}",
                        pci_bus_id=gpu_index,
                        pci_device_id=gpu_index,
                        pci_domain_id=gpu_index,
                        L2_cache_size="40MB",
                    )
                    self._mock_device_properties.append(device_properties)
                    pci_numa_node_path = (
                        self._get_corresponding_pci_numa_node_file_path(
                            device_properties=device_properties
                        )
                    )
                    self._mock_file_contents(
                        file_path=pci_numa_node_path,
                        contents=str(numa_node_index),
                    )

                for _ in range(num_l3_caches_per_numa_node):
                    lowest_logical_cpu_index_on_l3 = self._mock_num_logical_cpus
                    highest_logical_cpu_index_on_l3 = (
                        self._mock_num_logical_cpus
                        + 2 * num_physical_core_per_l3_cache
                        - 1
                    )
                    for logical_cpu_index in range(
                        self._mock_num_logical_cpus,
                        self._mock_num_logical_cpus
                        # Assume hyperthreaded
                        + 2 * num_physical_core_per_l3_cache,
                    ):
                        thread_siblings_range_str = (
                            f"{logical_cpu_index - 1}-{logical_cpu_index}"
                            if logical_cpu_index % 2
                            else f"{logical_cpu_index}-{logical_cpu_index + 1}"
                        )
                        self._mock_file_contents(
                            file_path=f"/sys/devices/system/cpu/cpu{logical_cpu_index}/topology/thread_siblings_list",
                            contents=thread_siblings_range_str,
                        )
                        # Unrelated file our logic should know to skip
                        self._mock_file_contents(
                            file_path=f"/sys/devices/system/cpu/cpu{logical_cpu_index}/cache/paulwuzhere",
                            contents="Data",
                        )
                        self._mock_file_contents(
                            file_path=f"/sys/devices/system/cpu/cpu{logical_cpu_index}/topology/physical_package_id",
                            contents=str(socket_index),
                        )
                        for cache_level in range(5):
                            self._mock_file_contents(
                                file_path=f"/sys/devices/system/cpu/cpu{logical_cpu_index}/cache/index{cache_level}/type",
                                contents="ShouldSkip" if cache_level == 4 else "Data",
                            )
                            self._mock_file_contents(
                                file_path=f"/sys/devices/system/cpu/cpu{logical_cpu_index}/cache/index{cache_level}/level",
                                contents=str(cache_level),
                            )
                            self._mock_file_contents(
                                file_path=f"/sys/devices/system/cpu/cpu{logical_cpu_index}/cache/index{cache_level}/shared_cpu_list",
                                contents=(
                                    f"{lowest_logical_cpu_index_on_l3}-{highest_logical_cpu_index_on_l3}"
                                    if cache_level == 3
                                    # Assume L1-2 are per physical core
                                    else thread_siblings_range_str
                                ),
                            )
                        self._mock_num_logical_cpus += 1
                self._mock_num_numa_nodes += 1
            self._mock_num_sockets += 1
        self._mock_file_contents(
            file_path="/sys/devices/system/node/possible",
            contents=f"0-{self._mock_num_numa_nodes - 1}",
        )