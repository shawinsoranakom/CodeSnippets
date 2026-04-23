def __init__(
        self,
        gm: torch.fx.GraphModule,
        example_inputs: Sequence[object] | None = None,
        shape_env: ShapeEnv | None = None,
        graph_id: int | None = None,
        cpp_wrapper: bool = False,
        aot_mode: bool = False,
        layout_opt: bool | None = None,
        extern_node_serializer: Callable[[list[ir.ExternKernelNode]], Any]
        | None = None,
        is_inference: bool = False,
        is_backward: bool = False,
        is_const_graph: bool = False,
        const_output_index: dict[str, int] | None = None,
        const_wrapper_code: str | None = None,
        const_kernel_code: str | None = None,
        const_module: GraphLowering | None = None,
        name: str | None = None,
        inputs_to_check: Sequence[int] | None = None,
        fx_wrapper: bool = False,
        get_decomp_fn: Callable[..., dict[Any, Callable[..., Any]]] | None = None,
    ) -> None:
        super().__init__(gm)
        self.get_decomp_fn = get_decomp_fn
        self.example_inputs = example_inputs
        self.layout_opt = (
            layout_opt
            if layout_opt is not None
            else self.decide_layout_opt(gm, is_inference=is_inference)
        )
        self.num_channels_last_conv = 0
        self.is_inference = is_inference
        self.is_backward = is_backward
        self.is_const_graph = is_const_graph
        self.const_wrapper_code = const_wrapper_code
        self.const_kernel_code = const_kernel_code
        self.const_module = const_module
        self.inputs_to_check = inputs_to_check
        self._defers_input_alignment = False

        self.extra_traceback = False  # we do our own error wrapping
        if shape_env is None:
            shape_env = ShapeEnv()
            self.reuse_shape_env = False
        else:
            self.reuse_shape_env = True
        self._shape_env = shape_env
        # We're going to mutate ras_by_symbol as we finish generating them
        self.ras_by_symbol: dict[sympy.Symbol | None, list[RuntimeAssert]] = (
            shape_env.deferred_runtime_asserts.copy()
        )
        self.bound_unbacked_symbols = OrderedSet[sympy.Symbol]()

        self.sizevars = SizeVarAllocator(shape_env)
        self.graph_input_names: list[str] = []
        self.graph_inputs: dict[str, TensorBox | TorchBindObject | sympy.Expr] = {}
        self.graph_inputs_original: dict[str, InputBuffer] = {}
        self.partition_maps: list[GraphPartitionMap] | None = None
        self.zero_dim_cpu_tensor_list: OrderedSet[str] = OrderedSet()
        self.device_types: OrderedSet[str] = (
            const_module.device_types if const_module else OrderedSet()
        )
        self.device_idxs: OrderedSet[int] = (
            const_module.device_idxs if const_module else OrderedSet()
        )
        self.device_type = "cpu"
        self.additional_buffer_deps: dict[str, OrderedSet[str]] = defaultdict(
            OrderedSet
        )
        self.additional_star_deps: dict[str, OrderedSet[str]] = defaultdict(OrderedSet)

        # Inplace padding may require Inductor to allocate slightly larger
        # tensor for padding.
        self.buffer_to_padded_size: dict[str, list[int]] = {}

        self.buffers: list[ir.Buffer] = []
        self.operations: list[ir.Operation] = []
        self.const_output_index: dict[str, int] = (
            const_output_index if const_output_index else {}
        )
        self.folded_constants: OrderedSet[str] = (
            OrderedSet(const_output_index.keys())
            if const_output_index
            else OrderedSet()
        )
        self.constants: dict[str, torch.Tensor] = (
            const_module.constants if const_module else {}
        )
        self.named_buffers: dict[str, torch.Tensor] = (
            const_module.named_buffers if const_module else {}
        )
        self.mutated_named_buffers: OrderedSet[torch.Tensor] = gm.meta.get(
            "mutated_named_buffers", OrderedSet()
        )
        self.named_parameters: dict[str, torch.Tensor] = (
            const_module.named_parameters if const_module else {}
        )
        self.torchbind_constants: dict[
            str, torch._C.ScriptObject | FakeScriptObject
        ] = {}
        self.opaque_value_type_classes: dict[str, type] = {}
        self.seen_subgraphs: dict[str, ir.Subgraph] = {}
        self.constant_reprs: dict[str, str] = {}
        self.removed_operations: OrderedSet[str] = OrderedSet()
        self.removed_buffers: OrderedSet[str] = OrderedSet()
        self.removed_inplace_buffers: OrderedSet[str] = OrderedSet()
        self.mutated_buffers: OrderedSet[str] = OrderedSet()
        self.sdpa_constraint_cache: dict[tuple, ir.IRNode] = {}
        self.never_reuse_buffers: OrderedSet[str] = OrderedSet()
        self.inplaced_to_remove: OrderedSet[str] = OrderedSet()
        self.device_ops: DeviceOpOverrides = None  # type: ignore[assignment]
        self.wrapper_code: PythonWrapperCodegen = None  # type: ignore[assignment]

        from torch._inductor.extern_node_serializer import extern_node_json_serializer

        self.extern_node_serializer: Callable[[list[ir.ExternKernelNode]], Any] = (
            extern_node_serializer
            if config.is_fbcode() and extern_node_serializer
            else extern_node_json_serializer
        )

        self.current_node: torch.fx.Node = None  # type: ignore[assignment]
        self.lists: dict[str, list[str]] = {}
        self.mutated_inputs: OrderedSet[str] = OrderedSet()
        self.mutated_input_idxs: list[int] = []
        self.name_to_buffer: dict[str, ir.Buffer] = {}
        self.name_to_users: defaultdict[str, list[ir.IRNode]] = defaultdict(list)
        self.name_to_op: dict[str, ir.Operation] = {}
        self.creation_time = time.time()
        self.name = name  # type: ignore[assignment]
        self.cpp_wrapper = cpp_wrapper
        self.fx_wrapper = fx_wrapper

        # record multi_kernel choice for cpp_wrapper so the second pass knows
        # which sub-kernel is picked. Copy cpp_wrapper to another variable
        # since cpp_wrapper flag is OrderedSet to false for the first pass of codegen.
        self.record_multi_kernel_choice = cpp_wrapper
        self.multi_kernel_to_choice: dict[str, str] = {}

        self.aot_mode = aot_mode
        self.graph_id = graph_id
        self.post_grad_graph_id = next(_post_grad_graph_counter)
        self.scheduler: torch._inductor.scheduler.Scheduler = None  # type: ignore[assignment]

        # record intermediate results for input of UsedDefinedTritonKernels
        # This will be used if autotuning is done in one pass.
        self.autotuning_inputs: list[torch.Tensor] | None = None
        self.autotuning_mapping: dict[str, dict[str, int]] | None = None
        self.autotuning_grids: dict[str, Any] | None = None

        # current_device is set only during codegen of a device-specific kernel
        # a graph can have many devices
        self.current_device: torch.device | None = None

        self.nodes_prefer_channels_last = (
            self.find_nodes_prefer_channels_last() if self.layout_opt else OrderedSet()
        )
        self._warned_fallback = OrderedSet(["aten.convolution_backward"])
        self.user_visible_output_strides = get_user_visible_output_strides(gm.graph)
        mark_nodes_dislike_padding(gm.graph, self.user_visible_output_strides)
        self.cache_key: str = ""  # This is the cache key for the compiled artifact
        self.cache_path: str = ""  # This is the path in the filesystem where the compiled artifact is stored
        self.cache_linemap: list[
            tuple[int, str]
        ] = []  # This is the linemap used by the profiler to mark custom compiled kernels getting run
        # Used if lowering encounters cases where cudagraphs are not supported
        self.disable_cudagraphs_reason: str | None = None

        # only keeping one node per device for stack trace purposes
        self.device_node_mapping: dict[torch.device, torch.fx.Node] = {}
        self.orig_gm: torch.fx.GraphModule = gm.__copy__()
        for k, v in self.orig_gm.named_buffers():
            self.named_buffers[k] = v
        for k, v in self.orig_gm.named_parameters():
            self.named_parameters[k] = v
        self.dynamo_flat_name_to_original_fqn = self.module.meta.get(  # type: ignore[operator, union-attr]
            "dynamo_flat_name_to_original_fqn", {}
        )
        self.allocated_constant_name: dict[str, str] = (
            const_module.allocated_constant_name if const_module is not None else {}
        )
        init_backend_registration()
        self.get_backend_features = functools.lru_cache(None)(get_backend_features)

        self.effectful_ops: dict[_EffectType, ir.Buffer] = {}
        # Track the buffers that we know is unaligned
        # This can either be a graph input or the output of fallback
        # kernels.
        self.unaligned_buffers: OrderedSet[str] = OrderedSet()
        self.no_fuse_buffer_names: OrderedSet[str] = OrderedSet()

        # Layout constraints for Triton template buffers.
        # Maps buffer name -> expected FixedLayout (computed speculatively without freezing)
        self.buffer_layout_constraints: dict[str, ir.FixedLayout] = {}

        self.low_precision_codegen_ops: OrderedSet[str] = OrderedSet()
        # more aggressive prologue fusion
        self.invoke_quant_ops: OrderedSet[str] = OrderedSet()

        # Below field is related to printing debug intermediate tensor values info for debugging
        self.all_codegen_kernel_names: OrderedSet[str] = OrderedSet()

        # state used by for KernelArgs.workspace
        self.workspace_id = itertools.count()

        # track the current placeholder index that we are processing
        self.placeholder_idx = -1

        self.bw_donated_idxs = get_donated_idxs()

        # Cache for dep size hints to avoid expensive recomputation
        self.dep_size_hint_cache: dict[tuple[Dep, bool], int] = {}