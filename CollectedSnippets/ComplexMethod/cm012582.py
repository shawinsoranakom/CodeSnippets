def create(
        cls,
        *,
        params: BlockParameters,
        constant_offset: sympy.Expr,
        range_trees: list[IterationRangesRoot],
        mask_vars: OrderedSet[str],
        get_max_block: Callable[[str], int],
        stride_sorter_cls: type[BlockParameters.StrideSorter],
        can_lift: bool = False,
    ) -> BlockDescriptorOptions:
        """Helper to create a BlockDescriptorOptions instance"""

        sizevars = V.graph.sizevars

        def lookup_size(exprs: Iterable[sympy.Expr]) -> list[sympy.Expr]:
            return [sizevars.lookup_precomputed_size(expr) for expr in exprs]

        # Look up precomputed sizes
        params.shape = lookup_size(params.shape)
        params.strides = lookup_size(params.strides)

        # Strip out dimensions of size 1.
        # Size 1 dimensions are redundant since the triton kernel shape
        # will be e.g. [YBLOCK, XBLOCK], so tl.reshape would just remove these
        # dimensions anyway
        singleton_dims = [
            sizevars.statically_known_equals(dim, 1) for dim in params.block_shape
        ]
        if all(singleton_dims):
            # Handle a pure singletons, e.g. [1, 1]
            singleton_dims[-1] = False

        # Drop singleton dimensions from the block descriptor.
        params = params.remove_dims(singleton_dims)

        # Maybe reorder dimensions based on strides
        # with tl.trans applied at load / store time
        params, stride_sorter = params.maybe_sort_with_stride_order(
            stride_sorter_cls=stride_sorter_cls, shape_env=V.graph._shape_env
        )

        # Strip out dimensions of stride 0.
        # These will be restored with tl.broadcast_to.
        broadcasting_dims = [
            sizevars.statically_known_equals(stride, 0) for stride in params.strides
        ]

        # Record the post-broadcast shape before broadcasting dims are removed.
        # The pre-broadcast shape is identical to this, except broadcasting dims are
        # replaced with 1.
        broadcast_shape = params.block_shape

        # Drop broadcasting dims from the block descriptor.
        params = params.remove_dims(broadcasting_dims)

        # Compute the final shape, adjusting for special kernel types.
        final_shape = [TritonSymbols.get_block_size(tree) for tree in range_trees]
        if V.kernel.no_x_dim:
            assert range_trees[0].prefix == "x"
            final_shape.pop(0)

        reduction_ndim = V.kernel.num_reduction_dims
        if (
            not V.kernel.inside_reduction
            and len(params.strides) == len(V.kernel.numels) - reduction_ndim
            and V.kernel.features.is_reduction()
        ):
            # Need to expand rank to match the rank used inside the reduction loop
            final_shape += [sympy.S.One] * reduction_ndim

        try:
            # Get permutation to sort strides in ascending order.
            # This is used as the order argument in tl.make_block_ptr
            order = utils.argsort_sym(V.graph._shape_env, params.strides)
        except AssertionError:
            # Symbolic shapes, failed to evaluate comparison expression
            order = list(reversed(range(len(params.strides))))

        result = cls(
            params=params,
            constant_offset=V.graph.sizevars.lookup_precomputed_size(constant_offset),
            order=order,
            mask_vars=mask_vars,
            final_shape=final_shape,
            broadcast_shape=broadcast_shape,
            broadcasting_dims=broadcasting_dims,
            stride_sorter=stride_sorter,
            can_lift=can_lift,
        )
        result.compute_boundary_check(get_max_block, range_trees)
        return result