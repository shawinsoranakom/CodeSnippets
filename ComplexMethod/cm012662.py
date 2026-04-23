def codegen_node_schedule(self, kernel_features: SIMDKernelFeatures):
        """
        Generate code for nodes in kernel_features
        """
        node_schedule = kernel_features.node_schedule

        tiling, tiling_score = self.get_tiling_and_scores(
            node_schedule,
            kernel_features.numel,
            kernel_features.reduction_numel,
            kernel_features.coalesce_analysis,
        )
        kernels = self.create_kernel_choices(
            kernel_features,
            [tiling],
            {"features": kernel_features, "tiling_scores": tiling_score},
        )
        for kernel in kernels:
            self.codegen_node_schedule_with_kernel(node_schedule, kernel)
        MultiKernel.merge_workspaces_inplace(kernels)

        # Collect config_patches from operations (e.g., decomposition ops with
        # coordinate_descent_tuning) and apply during kernel codegen
        config_patches = self._collect_config_patches(node_schedule)

        for kernel in kernels:
            with V.set_kernel_handler(kernel), config.patch(**config_patches):
                src_code = kernel.codegen_kernel()
            kernel_name = self.define_kernel(src_code, node_schedule, kernel)
            log.debug("Generating kernel code with kernel_name: %s", kernel_name)
            kernel.kernel_name = kernel_name
            kernel.code_hash = code_hash(src_code)
        del kernel

        final_kernel: SIMDKernel | MultiKernel
        if len(kernels) > 1:
            final_kernel = MultiKernel(kernels)
        else:
            (final_kernel,) = kernels

        with V.set_kernel_handler(final_kernel):
            for node in kernel_features.scheduler_nodes():
                node.mark_run()

        # filter out NodeScheduleMarker
        base_scheduler_nodes = [
            node for node in node_schedule if isinstance(node, BaseSchedulerNode)
        ]
        self.codegen_comment(base_scheduler_nodes, final_kernel.kernel_name)
        if config.cpp.enable_kernel_profile:
            V.graph.wrapper_code.write_kernel_context_guard_begin()
            V.graph.wrapper_code.write_kernel_context_guard(
                final_kernel.kernel_name,
                base_scheduler_nodes,  # type: ignore[arg-type]
            )
        final_kernel.call_kernel(final_kernel.kernel_name)
        if config.cpp.enable_kernel_profile:
            V.graph.wrapper_code.write_kernel_context_guard_end()

        if config.nan_asserts:
            final_kernel.codegen_nan_check()
        if config.warn_mix_layout:
            final_kernel.warn_mix_layout(kernels[0].kernel_name)

        V.graph.removed_buffers |= final_kernel.removed_buffers
        V.graph.inplaced_to_remove |= final_kernel.inplaced_to_remove

        if (
            V.graph.wrapper_code.supports_intermediate_hooks  # type: ignore[has-type]
            and config.generate_intermediate_hooks
        ):
            # Not every node in the schedule will actually be live on output;
            # we can't check dead buffers.
            live_outs = kernels[0].args.live_output_buffers()
            for node in kernel_features.scheduler_nodes():
                name = node.get_name()
                if name not in live_outs:
                    continue
                assert node.node is not None
                origin_node = node.node.get_origin_node()
                if origin_node is not None:
                    counters["inductor"]["intermediate_hooks"] += 1
                    V.graph.wrapper_code.writeline(
                        f"run_intermediate_hooks({origin_node.name!r}, {name})"
                    )

        self.free_buffers_in_scheduler()