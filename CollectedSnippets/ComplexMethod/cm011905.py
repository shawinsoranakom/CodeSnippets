def __init__(
        self,
        kernel_name,
        input_nodes: tuple[ir.IRNode, ...],
        output_node,
        defines,
        num_stages,
        num_warps,
        grid_fn,
        meta,
        call_sizes,
        num_consumer_groups=0,
        num_buffers_warp_spec=0,
        use_jit=False,
        tma_store=False,
        transpose_discontiguous_tensor_descriptors_override=None,
        prefix_args=0,
        suffix_args=0,
        epilogue_fn=identity,
        subgraphs: list[ir.ComputedBuffer] | None = None,
        workspace_arg: WorkspaceArg | None = None,
        prologue_loads_all_inputs=False,
        hint_override: int | None = None,
        triton_meta: dict[str, object] | None = None,
        always_freeze_layout: bool = False,
        index_dtype_override: str | None = None,
    ) -> None:
        if tma_store:
            pass
        numel = sympy_product(output_node.get_size())
        if tma_store:
            assert len(output_node.get_size()) == 2, (
                "TMA store only supported for 2D with templates"
            )
            tiling = {
                "x": output_node.get_size()[0],
                "y": output_node.get_size()[1],
                "r0_": sympy.S.One,
            }
        else:
            tiling = {
                "x": numel,
                "r0_": sympy.S.One,
            }
        super().__init__(
            tiling,
            features=SIMDKernelFeatures([], numel),
            hint_override=hint_override,
        )
        if tma_store:
            # By default `construct_range_trees` will return the range_trees in the order
            # ["z", "y", "x", "r0_", "r1_"] (see simd.py:all_prefixes)
            # and this order defines what the kernel block shape will be. So if the template
            # input / output has requested e.g. ["x", "y"], `construct_range_trees` will still return the
            # trees in the order ["y", "x"]. This would mean that the template would need to transpose
            # the loaded value.
            # The below sorts the range trees according to that required by the caller
            prefix_to_range_tree = {rt.prefix: rt for rt in self.range_trees}
            pw_sorted_range_trees = []
            reduction_idx = None
            for i, prefix in enumerate(tiling):
                rt = prefix_to_range_tree[prefix]

                if rt.is_reduction:
                    reduction_idx = i
                    break
                rt.index = i
                rt.grid_dim = i
                rt.tensor_dim = i
                pw_sorted_range_trees.append(rt)
            self.range_trees = pw_sorted_range_trees + self.range_trees[reduction_idx:]

        self.input_nodes = input_nodes
        self.output_node = output_node
        self.named_input_nodes = {}  # type: ignore[var-annotated]
        self.defines = defines
        self.kernel_name = kernel_name
        self.use_jit = use_jit
        self.tma_store = tma_store
        self.transpose_discontiguous_tensor_descriptors_override = (
            transpose_discontiguous_tensor_descriptors_override
        )
        self.num_stages = num_stages
        self.num_warps = num_warps
        self.num_consumer_groups = num_consumer_groups
        self.num_buffers_warp_spec = num_buffers_warp_spec
        self.grid_fn = grid_fn
        self.meta = meta
        self.call_sizes = call_sizes
        # for templates with fixed epilogues
        self.prefix_args = prefix_args
        self.suffix_args = suffix_args
        # pyrefly: ignore [invalid-type-var]
        self.epilogue_fn = epilogue_fn
        self.render_hooks = {}  # type: ignore[var-annotated]
        self.triton_meta: dict[str, object] | None = triton_meta
        self._index_dtype_override = index_dtype_override
        # For Templated Attention this can be a list of ir.Subgraph
        self.subgraphs: list[ir.ComputedBuffer] | None = subgraphs

        # Some templates use extra global memory as a workspace
        self.workspace_arg = workspace_arg
        if workspace_arg is not None:
            self.args.workspace_args.append(workspace_arg)

        # The following attributes (body, template_mask, output_val) are all
        # used for triton kernel codegen.
        # They are swapped onto the TritonTemplateKernel object by
        # `set_subgraph_body`
        self.subgraph_bodies: dict[str, SubgraphInfo] = {}

        # input buffers which we are allowed to prologue fuse into
        self.prologue_supported_inputs: OrderedSet[str] = OrderedSet()

        # input buffers which we are fusing into
        self.prologue_fused_inputs: OrderedSet[str] = OrderedSet()
        # input buffers which we are fusing into, which preserve a zero mask
        self.prologue_fused_inputs_preserve_zero: OrderedSet[str] = OrderedSet()

        # The following attributes are all used for triton kernel codegen.
        # They are swapped onto the TritonTemplateKernel object by
        # `set_subgraph_body`
        # NB: the names here must match the fields in SubgraphInfo
        self.body: IndentedBuffer = FakeIndentedBuffer()
        self.compute: IndentedBuffer = FakeIndentedBuffer()
        self.indexing_code: IndentedBuffer = FakeIndentedBuffer()
        self.loads: IndentedBuffer = FakeIndentedBuffer()
        self.stores: IndentedBuffer = FakeIndentedBuffer()
        self.template_mask: str | None = None
        self.template_out_shape: str | tuple[str] | None = None
        self.ops_handler: V.WrapperHandler | None = None  # type: ignore[name-defined]
        self.root_var_renames: dict[str, str] = {}

        # When caching is enabled, the generated code is not dependent on the input nodes names, or
        # symbolic sizes names.
        # However, some of the variables returned by generate_and_load that are computed during the
        # triton template expansions (code generation) are dependent on those.
        # In order to cache the code generation and avoid redoing it for similar inputs that varies only by
        # input names or symbol names, we do a record and replay method.
        # During template expansions we record all function calls that change input_dependent_preserved_state
        # and replay them on a cache hit to regenerate them.
        self.cached_replay_events: RecordedEventsType | None = None

        # Update each time an input is marked frozen, used to replay the freezing of inputs on a cache hit.
        self.frozen_layouts_cnt = 0

        # When prologue_loads_all_inputs is true, prologue_supported_inputs is populated during def_kernel
        # by adding all inputs.
        self.prologue_loads_all_inputs = prologue_loads_all_inputs

        # When always_freeze_layout is True, get_stride_and_maybe_freeze_layout will
        # always freeze the layout immediately, bypassing layout constraints.
        # This is used by FlexAttention templates which require frozen layouts.
        self.always_freeze_layout = always_freeze_layout

        # Extra functions to be exposed during partial template rendering.
        self.extra_template_env_fns: list[Callable[..., Any]] = []

        # Tracking for intermediate variables
        self.tmp_var_ctr = itertools.count()