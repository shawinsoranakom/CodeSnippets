def _codegen_mix_order_reduction(self, node1, node2):
        numel, rnumel = scheduler.MixOrderReduction.get_numel_rnumel(node1)

        def _pick_split_size():
            # the overridden has highest priority
            if config.triton.mix_order_reduction_split_size is not None:
                return config.triton.mix_order_reduction_split_size

            # heuristics based on number of SMs
            device_prop = DeviceProperties.create(node1.get_device())
            num_sm = device_prop.multi_processor_count
            estimated_num_splits = num_sm * 8

            # split_size is decided based on hint.
            # optimization_hint is fine here: the result is clamped to [16, 128],
            # so any fallback value still produces a valid split size.
            numel_hint = V.graph.sizevars.optimization_hint(numel)
            split_size = max(last_power_of_2(numel_hint // estimated_num_splits), 16)
            split_size = min(split_size, 128)
            return split_size

        split_size = _pick_split_size()

        # pyrefly: ignore [bad-assignment]
        metrics.codegen_mix_order_reduction += 1

        # split epilogue out of node2
        node2_reductions, node2_epilogue = self._split_mix_order_reduction_epilogue(
            node2
        )

        converted_nodes = []
        for subnode in node2_reductions:
            subnode.cancel_reduction_split()
            converted = subnode.extract_pw_from_reduction()
            converted.swap_pw_red_dimension()
            converted_nodes.append(converted)
        node_schedule = self.generate_node_schedule(
            node1.get_nodes() + converted_nodes, numel, rnumel
        )
        kernel_features = SIMDKernelFeatures(node_schedule, numel, rnumel)

        # The autotuning is skipped in deterministic mode
        if (
            not torch._inductor.config.deterministic
            and config.triton.mix_order_reduction_split_size is None
            and (
                config.triton.mix_order_reduction_autotune_split_size
                or config.max_autotune
                or config.coordinate_descent_tuning
            )
        ):

            def _bench(candidate_split_size):
                _, _, src_code = self._generate_kernel_code_for_mix_order_reduction(
                    kernel_features,
                    split_size=candidate_split_size,
                    for_benchmark=True,
                )
                mod = PyCodeCache.load(src_code)
                ms, _ = self.benchmark_codegened_module(mod)
                return ms

            split_size = CoordescTuner.autotune_single_field(
                _bench,
                split_size,
                8,
            )

        kernel, ws_name, src_code = self._generate_kernel_code_for_mix_order_reduction(
            kernel_features,
            split_size=split_size,
            for_benchmark=False,
        )

        # rename intermediate reduction output to final reduction
        # output
        is_split_reduction = bool(node2_reductions[0].node._split_size)
        rename = {}
        if is_split_reduction:
            for subnode in node2_reductions:
                bufname = subnode.get_outputs()[0].node.get_name()
                username = (
                    subnode.get_outputs()[0]
                    .users[0]
                    .node.get_outputs()[0]
                    .node.get_name()
                )
                rename[bufname] = username
                assert self.scheduler
                self.scheduler.removed_ops.add(
                    subnode.get_outputs()[0].users[0].node.get_name()
                )
                V.graph.removed_buffers.add(bufname)

            for partial_accum in kernel.saved_partial_accumulate:
                partial_accum.buffer_name = rename.get(
                    partial_accum.buffer_name, partial_accum.buffer_name
                )

        kernel_name = self.define_kernel(src_code, node_schedule, kernel)
        kernel.kernel_name = kernel_name
        kernel.code_hash = code_hash(src_code)

        with V.set_kernel_handler(kernel):
            for node in kernel_features.scheduler_nodes():
                # No need to allocate buffer for split reduction
                # since we are gonna to allocate workspace to store the
                # intermediate reduction reduction
                if node.get_outputs()[0].node.get_name() not in rename:
                    node.mark_run()

        V.graph.wrapper_code.make_comment("# Call mix order reduction kernel")
        self.codegen_comment(node_schedule, None)
        # workspace args is still needed after the call
        kernel.call_kernel(kernel.kernel_name, deallocate_ws=False)
        V.graph.removed_buffers |= kernel.removed_buffers
        V.graph.inplaced_to_remove |= kernel.inplaced_to_remove

        # a extra round of reduction
        assert len(converted_nodes) == len(kernel.saved_partial_accumulate)
        nsplit = V.graph.wrapper_code.codegen_python_sizevar(
            (numel + split_size - 1) // split_size
        )
        for idx, partial_accum in enumerate(kernel.saved_partial_accumulate):
            buffer_name = partial_accum.buffer_name

            stride_str = f"({nsplit}) * ({rnumel})"
            start = f"{idx} * {stride_str}"
            end = f"({idx} + 1) * {stride_str}"
            reduction_type2op = {
                "min": "amin",
                "max": "amax",
            }
            opname = reduction_type2op.get(
                partial_accum.reduction_type, partial_accum.reduction_type
            )

            # Check if the original reduction used keepdim=True by comparing dimensions.
            # Without keepdim, reduction produces [rnumel]; with keepdim, [1, rnumel].
            buffer = V.graph.get_buffer(buffer_name)
            keepdim = buffer is not None and len(buffer.get_layout().size) > 1

            final_reduce = f"{buffer_name} = {ws_name}[{start} : {end}].view({nsplit}, {rnumel}).{opname}(dim=0, keepdim={keepdim})"

            # The workspace tensor is in torch.float, need a cast if the buffer is
            # not.
            if (buffer_dtype := V.graph.get_dtype(buffer_name)) != torch.float:
                final_reduce += f".to({buffer_dtype})"
            V.graph.wrapper_code.writeline(final_reduce)
            # mark the buffer as allocated, so we don't try to allocate
            # it again when it's later used
            V.graph.wrapper_code.allocated.add(buffer_name)

        kernel.deallocate_workspaces()

        if node2_epilogue:
            self._codegen_nodes(node2_epilogue)

        self.free_buffers_in_scheduler()