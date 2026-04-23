def generate_combo_kernel_code(
        self,
        subkernel_nodes: list[BaseSchedulerNode],
        custom_part_algorithm: bool,
        enable_autotune: bool,
        mixed_sizes: bool,
        only_gen_src_code: bool = False,
    ) -> list[tuple[str | None, Any, Any]]:
        """
        Generate kernel code for combo kernel partitions.

        Partitions subkernel_nodes using horizontal_partition(), then generates
        kernel code for each partition. Single-node partitions are generated as
        regular kernels, while multi-node partitions use ComboKernel.

        Returns a list of (src_code, kernel, node_group) tuples.
        """
        from .triton import TritonKernel
        from .triton_combo_kernel import ComboKernel

        # This is currently the only type supported by this method
        assert issubclass(self.kernel_type, TritonKernel)

        fused_node_lists = [node.get_nodes() for node in subkernel_nodes]
        node_schedule_map: dict[Any, NodeInfo] = {}
        for pn, nodes in zip(subkernel_nodes, fused_node_lists):
            _, (numel, rnumel) = max(nodes, key=lambda x: int(x.is_reduction())).group
            node_schedule = self.generate_node_schedule(nodes, numel, rnumel)
            tiling = self.select_tiling(node_schedule, numel, rnumel)
            features = SIMDKernelFeatures(node_schedule, numel, rnumel)
            is_persistent_reduction = (
                features.is_reduction()
                and V.choices.should_use_persistent_reduction(
                    features, cooperative_reduction=False
                )
            )
            node_schedule_map[pn] = NodeInfo(
                node_schedule=node_schedule,
                tiling=tiling,
                numel=numel,
                rnumel=rnumel,
                features=features,
                is_persistent_reduction=is_persistent_reduction,
            )

        partitions = ComboKernel.horizontal_partition(
            nodes=subkernel_nodes,
            triton_scheduling=self,
            custom_algorithm=custom_part_algorithm,
            node_info_map=node_schedule_map,
        )
        log.debug(
            "ComboKernels: %d nodes partitioned into %s groups",
            len(subkernel_nodes),
            [len(p) for p in partitions],
        )
        kernel_code_list = []
        for node_group in partitions:
            if len(node_group) == 0:
                continue

            if len(node_group) == 1:
                # Single-node partition
                node_info = node_schedule_map[node_group[0]]
                if only_gen_src_code:
                    # Skip code generation - caller has cached benchmark results
                    kernel_code_list.append((None, None, node_group))
                else:
                    # Generate regular kernel
                    kernel = self.kernel_type(
                        node_info.tiling,
                        features=node_info.features,
                    )
                    self.process_kernel(
                        kernel, node_info.node_schedule, only_gen_src_code
                    )
                    with V.set_kernel_handler(kernel):
                        src_code = kernel.codegen_kernel()
                    # pyrefly: ignore [bad-argument-type]
                    kernel_code_list.append((src_code, kernel, node_group))
            else:
                # Multi-node: create ComboKernel with combo subkernels
                kernel = ComboKernel(
                    triton_kernel_cls=self.kernel_type,
                    enable_autotune=enable_autotune,
                    mixed_sizes=mixed_sizes,
                )
                for pn in node_group:
                    node_info = node_schedule_map[pn]
                    subkernel = ComboKernel.create_triton_kernel(
                        node_info.tiling,
                        features=node_info.features,
                        optimize_mask=not mixed_sizes,
                        triton_kernel_cls=self.kernel_type,
                    )
                    self.process_kernel(
                        kernel.create_sub_kernel(subkernel),
                        node_info.node_schedule,
                        only_gen_src_code,
                    )

                src_code = kernel.codegen_kernel()
                # pyrefly: ignore [bad-argument-type]
                kernel_code_list.append((src_code, kernel, node_group))
        # pyrefly: ignore [bad-return]
        return kernel_code_list