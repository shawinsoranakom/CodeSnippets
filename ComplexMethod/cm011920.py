def generate(  # type: ignore[override]
        self,
        input_nodes: tuple[ir.IRNode, ...],
        layout: ir.Layout,
        num_stages: int,
        num_warps: int,
        num_consumer_groups: int = 0,
        num_buffers_warp_spec: int = 0,
        prefix_args: int = 0,
        suffix_args: int = 0,
        epilogue_fn: Callable[..., Any] | None = identity,
        epilogue_fn_hash: str | None = None,
        subgraphs: list[ir.Buffer] | None = None,
        mutated_inputs: list[ir.IRNode] | None = None,
        call_sizes: Sequence[sympy.core.symbol.Symbol] | None = None,
        workspace_arg: WorkspaceArg | None = None,
        generate_with_caching=False,
        hint_override: int | None = None,
        tma_store: bool = False,
        transpose_discontiguous_tensor_descriptors_override: bool | None = None,
        triton_meta: dict[str, Any] | None = None,
        **kwargs,
    ):
        """This function generates a TritonTemplateCaller

        Args:
            input_nodes: List of input nodes
            layout: Output layout
            num_stages: Number of stages for triton launch
            num_warps: Number of warps for triton launch
            prefix_args: Number of input nodes to be passed as arguments
            suffix_args: Number of input nodes to be passed as arguments
            epilogue_fn: Optional epilogue function to be called on the output
            subgraphs: Optional subgraphs to be passed as arguments, these will be inlined
                into the triton template string
            mutated_inputs: Optional list of input nodes that are mutated by the kernel, this is helpful
                if you need to return multiple outputs. You can pass them as inputs and mark them as
                being mutated by the kernel.
        """
        # HACK: Triton currently breaks if TF32 floats are requested, but the CUDA
        # capability doesn't support them.  This is a bug in Triton, but for now we'll
        # patch around it here.  See https://github.com/triton-lang/triton/issues/3011
        # for one example issue with this problem.
        if torch.cuda.is_available() and not torch.cuda.is_tf32_supported():
            kwargs["ALLOW_TF32"] = "False"

        if call_sizes is None:
            call_sizes = layout.size

        result = self.generate_and_load(
            input_nodes,
            num_stages,
            num_warps,
            call_sizes,
            prefix_args,
            suffix_args,
            epilogue_fn,
            epilogue_fn_hash,
            subgraphs,
            workspace_arg,
            num_consumer_groups,
            num_buffers_warp_spec,
            layout,
            kwargs,
            generate_with_caching and self._cache_codegen_enabled_for_template,
            hint_override=hint_override,
            tma_store=tma_store,
            transpose_discontiguous_tensor_descriptors_override=transpose_discontiguous_tensor_descriptors_override,
            triton_meta=triton_meta,
        )

        # May happen as result of dev by 0.
        if result is None:
            return None

        # We expect the input_buffer order to be [*input_nodes, *captured_buffers]
        expected_input_args = tuple(unique(x.get_name() for x in input_nodes))
        assert (
            result.input_call_args[: len(expected_input_args)] == expected_input_args
        ), (
            result.input_call_args,
            expected_input_args,
        )

        # `kernel_input_nodes` are the actual inputs that will be passed to the kernel,
        # so e.g. views of the same input are not included. `codegen_input_nodes`
        # includes views of inputs to preserve the kernel semantics. The shape and
        # strides of `codegen_input_nodes` will be used to infer read/writes in
        # TemplateBuffer.extract_read_writes
        kernel_input_nodes = tuple(
            [V.graph.get_buffer(k) for k in result.input_call_args]
        )
        # Here we have (*input_nodes, *captured_buffers)
        codegen_input_nodes = (
            tuple(input_nodes) + kernel_input_nodes[len(expected_input_args) :]
        )

        extra_args = tuple(
            V.graph.sizevars.optimization_hint_with_override(
                sympy.expand(e),
                hint_override=hint_override,
            )
            for e in result.kernel_args_sizevars_keys
        )

        kernel_hash_name = f"triton_{self.name}_{next(self.index_counter)}"

        # Extract workspace metadata for async autotuning (don't create tensor here
        # as it can't be pickled for subprocess communication)
        workspace_size_bytes: int | None = None
        workspace_zero_fill = False
        workspace_args = []
        if workspace_arg is not None:
            ws_count = V.graph.sizevars.optimization_hint(workspace_arg.count)
            workspace_size_bytes = ws_count * get_dtype_size(workspace_arg.dtype)
            workspace_zero_fill = (
                workspace_arg.zero_mode != WorkspaceZeroMode.UNINITIALIZED
            )

            workspace_args.append(WORKSPACE_ARG_PLACEHOLDER)

        options = result.kernel_options

        def make_kernel_render(out_node, hint_override: int | None = None):
            assert result is not None
            # Create a new unique name for the workspace arg buffer for each render
            # to prevent buffer reuse of the same workspace arg
            kernel_workspace_arg = workspace_arg
            if workspace_arg is not None:
                kernel_workspace_arg = WorkspaceArg(
                    count=workspace_arg.count,
                    zero_mode=workspace_arg.zero_mode,
                    device=workspace_arg.device,
                    outer_name=WorkspaceArg.unique_name(),
                    inner_name=workspace_arg.inner_name,
                    dtype=workspace_arg.dtype,
                )
            kernel = self.kernel_type(
                kernel_name=str(Placeholder.KERNEL_NAME),
                output_node=out_node,
                workspace_arg=kernel_workspace_arg,
                use_jit=False,
                hint_override=hint_override,
                tma_store=tma_store,
                transpose_discontiguous_tensor_descriptors_override=transpose_discontiguous_tensor_descriptors_override,
                triton_meta=triton_meta,
                **options,
            )
            render = functools.partial(
                kernel.render,
                self.template,
                kwargs,
            )
            return kernel, render

        # create the BenchmarkRequest
        assert result.mod.__file__ is not None

        grid = self.grid(
            *V.graph.sizevars.optimization_hints_with_override(
                call_sizes,
                hint_override=hint_override,
            ),
            kwargs,
        )
        bmreq_cls: type[TritonBenchmarkRequest]
        if layout.device.type == "cpu":
            bmreq_cls = TritonCPUBenchmarkRequest
        else:
            bmreq_cls = TritonGPUBenchmarkRequest
        bmreq = bmreq_cls(
            module_path=result.mod.__file__,
            module_cache_key=result.mod.key,
            kernel_name=f"triton_{self.name}",
            extra_args=[*extra_args, *workspace_args, *grid],
            num_stages=num_stages,
            num_warps=num_warps,
            num_consumer_groups=num_consumer_groups,
            num_buffers_warp_spec=num_buffers_warp_spec,
            matrix_instr_nonkdim=kwargs.get("matrix_instr_nonkdim", 0),
            waves_per_eu=kwargs.get("waves_per_eu", 0),
            kpack=kwargs.get("kpack", 2),
            workspace_size=workspace_size_bytes,
            workspace_zero_fill=workspace_zero_fill,
            input_tensor_meta=TensorMeta.from_irnodes(kernel_input_nodes),  # type: ignore[arg-type]
            output_tensor_meta=TensorMeta.from_irnodes(layout),
        )

        # Convolution-specific parameters to include in logging
        CONV_TUNABLE_KEYS = [
            "KERNEL_H",
            "KERNEL_W",
            "KERNEL_D",
            "STRIDE_H",
            "STRIDE_W",
            "STRIDE_D",
            "PADDING_H",
            "PADDING_W",
            "PADDING_D",
            "GROUPS",
            "UNROLL",
        ]

        return TritonTemplateCaller(
            kernel_hash_name,
            codegen_input_nodes,
            layout,
            make_kernel_render,
            result.extra.strip("-").replace("-", ", "),
            bmreq,
            log_info={
                "tile_shape": str(
                    (
                        kwargs.get("BLOCK_M", -1),
                        kwargs.get("BLOCK_K", -1),
                        kwargs.get("BLOCK_N", -1),
                    )
                ),
                "num_stages": num_stages,
                "num_warps": num_warps,
                "GROUP_M": kwargs.get("GROUP_M", -1),
                "allow_tf32": str(kwargs.get("ALLOW_TF32")),
                "acc_type": str(kwargs.get("ACC_TYPE")),
                "matrix_instr_nonkdim": kwargs.get("matrix_instr_nonkdim", 0),
                "waves_per_eu": kwargs.get("waves_per_eu", 0),
                "kpack": kwargs.get("kpack", 2),
                "epilogue_subtile": kwargs.get("EPILOGUE_SUBTILE", 0),
                **{
                    k: kwargs[k]
                    for k in AlgorithmSelectorCache.FLEX_ATTENTION_TUNABLE_KEYS
                    if k in kwargs
                },
                **{k: kwargs[k] for k in CONV_TUNABLE_KEYS if k in kwargs},
            },
            mutated_inputs=mutated_inputs,
            workspace_arg=workspace_arg,
            allowed_prologue_inps=result.prologue_supported_inputs,
            hint_override=hint_override,
        )