def __init__(
        self,
        tiling: dict[str, sympy.Expr],
        features: SIMDKernelFeatures,
        pid_cache: dict[str, str] | None = None,
        override_persistent_reduction: bool | None = None,
        override_cooperative_reduction: bool | None = None,
        tiling_scores: dict[str, sympy.Expr] | None = None,
        mix_order_reduction: bool = False,
    ) -> None:
        if pid_cache is None:
            pid_cache = {}
        super().__init__()
        self.features = features
        self.mutations = features.get_mutations()
        self.body = IndentedBuffer()
        self.indexing_code = IndentedBuffer()
        self.numels = {
            prefix: V.graph.sizevars.simplify(val) for prefix, val in tiling.items()
        }
        self.range_trees: list[IterationRangesRoot] = []
        self.range_tree_nodes: dict[sympy.Symbol, IterationRangesEntry] = {}
        self.iter_vars_count = itertools.count()
        self.inside_reduction = features.is_reduction()
        self.cooperative_reduction: bool = (
            override_cooperative_reduction
            if override_cooperative_reduction is not None
            else self.should_use_cooperative_reduction()
        )
        self.tiling_scores: dict[str, sympy.Expr] | None = tiling_scores
        self.tiling: dict[str, sympy.Expr] = tiling
        self.persistent_reduction: bool = (
            override_persistent_reduction
            if override_persistent_reduction is not None
            else self.should_use_persistent_reduction()
        )
        self.mix_order_reduction: bool = mix_order_reduction
        self.no_x_dim = self.want_no_x_dim()
        self.code_hash: str | None = None
        # Info to enable multiple store_output calls for epilogue subtiling
        self.store_output_ctr = itertools.count()
        self.is_native_matmul = False
        if config.triton.native_matmul:
            for node in self.features.node_schedule:
                if (
                    isinstance(node, scheduler.SchedulerNode)
                    and isinstance(node.node, ir.ComputedBuffer)
                    and node.node.get_reduction_type() == "dot"
                ):
                    self.is_native_matmul = True
                    break

        # define this in a closure to make cache local to object
        @functools.cache
        def simplify_indexing(index: sympy.Expr):
            index = V.graph.sizevars.simplify_with_ranges(index, self.var_ranges())
            for tree in self.range_trees:
                index = self.combine_contiguous_dims(index, tree)

            return self.combine_modular_indexing_pairs(index)

        self.simplify_indexing = simplify_indexing
        self.initialize_range_tree(pid_cache)

        self.rsplit_size = 0
        self.saved_partial_accumulate: list[PartialAccumulate] = []