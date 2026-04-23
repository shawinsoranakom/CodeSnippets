def indexing(
        self,
        index: sympy.Expr,
        *,
        copy_shape: str | tuple[str] | None = None,
        dense_indexing=False,
        override_mask=None,
        block_ptr=False,
        tma_compatibility_checker: TMACompatibilityChecker | None = None,
        mask_constant_index=False,
    ):
        """
        Compute the index and mask to pass to tl.load() or tl.store()
        """
        index = self.prepare_indexing(index)
        index_vars = index.free_symbols
        has_rindex = False

        mask_vars: OrderedSet[str] = OrderedSet()
        for var in sorted(index_vars, key=operator.attrgetter("name")):
            assert isinstance(var, sympy.Symbol)
            has_rindex = has_rindex or symbol_is_type(
                var, TritonSymbols.reduction_types
            )
            if override_mask:
                pass
            elif symbol_is_type(var, SymT.TMP):
                # indirect indexing
                cse_var = self.cse.varname_map[var.name]
                mask_vars.update(cse_var.mask_vars)
            elif symbol_is_type(
                var,
                (
                    SymT.UNBACKED_INT,
                    SymT.SIZE,
                    SymT.PRECOMPUTED_SIZE,
                    SymT.INDEX,
                    SymT.FLOAT,
                    SymT.UNBACKED_FLOAT,
                ),
            ):
                pass
            else:
                # var is one of xN, yN, r0_N or r1_N
                prefix_matches = [
                    prefix_str[symt]
                    for symt in TritonSymbols.block_types
                    if symbol_is_type(var, symt)
                ]
                if len(prefix_matches) == 0:
                    pass
                assert len(prefix_matches) == 1, f"Ambiguous type: {var.name}"
                mask_vars.add(f"{prefix_matches[0]}mask")

        need_dense = (
            config.triton.dense_indexing
            or dense_indexing
            or self._load_mask is not None
        ) and index != 0

        have_dense = True
        have_loop_vars = False
        dense_mask_vars: OrderedSet[str] = OrderedSet()

        for tree in self.active_range_trees():
            if index_vars.intersection(tree.var_list):
                have_loop_vars = True
            else:
                have_dense = False
            dense_mask_vars.add(f"{tree.prefix}mask")

        if (
            (
                (block_ptr and self.allow_block_ptr and config.triton.use_block_ptr)
                or (
                    tma_compatibility_checker
                    and tma_compatibility_checker.can_use_tma()
                )
            )
            and not override_mask
            and not self._load_mask
            and len(mask_vars - dense_mask_vars) == 0
            and not self.is_indirect_indexing(index)
            and have_loop_vars
            # workaround https://github.com/triton-lang/triton/issues/2821
            and self.index_dtype == "tl.int32"
        ):

            def match_affine_block(
                index: sympy.Expr, range_tree: IterationRangesRoot
            ) -> BlockParameters | None:
                """
                Matches expressions of the form:
                    idx = s * xindex

                This implies stride (s,), and shape (XBLOCK,).
                """
                stride = BlockPatternMatcher.match_affine_block_expr(
                    index, range_tree.symbol()
                )
                if stride is None:
                    return None

                return BlockParameters(
                    shape=[range_tree.numel],
                    block_shape=[TritonSymbols.get_block_size(range_tree)],
                    strides=[stride],
                    offsets=[TritonSymbols.get_block_offset(range_tree)],
                )

            def match_mod_div_block(
                index: sympy.Expr, range_tree: IterationRangesRoot
            ) -> BlockParameters | None:
                """
                Matches higher-dimensional blocks coming from FloorDiv and ModularIndexing.

                Example expression to match:
                   sN * ((rindex//(d1 * ... * d(N-1))))
                       + s1 * ModularIndexing(rindex, 1, d1)
                       + ...
                       + s(N-1) * ModularIndexing(rindex, d1 * ... * d(N-2), d(N-1))

                This iterates over a block of shape (dN, ..., d1) and stride
                (sN, ..., s1). (d1,...,d(N-1)) and (s1,...,sN) are
                wildcards that we match.

                Note that dN does not appear in the expression, but we solve for it
                using range tree numels and the other dims.
                """
                index_var = range_tree.symbol()

                # Bound the possible number of dims. We use the following heuristics:
                # - At least one dim for each range tree node.
                # - At least one dim for every FloorDiv or ModularIndexing op.
                # - At least 2 dims to pattern match.
                denom, modulo = sympy.symbols(
                    "denom modulo",
                    cls=functools.partial(sympy.Wild, exclude=[index_var]),
                )

                num_dims = max(
                    2,
                    # range_tree.nodes only includes the entries for the range tree
                    # len(range_tree.nodes) <= self.range_tree_nodes
                    len(range_tree.nodes),
                    (
                        index.count(FloorDiv(index_var, denom))
                        + index.count(ModularIndexing(index_var, denom, modulo))
                    ),
                )

                # [Note: Precomputed replacements with BlockPatternMatch]
                # If there are precomputed replacements in an expression e.g.
                # ModularIndexing(d0 * d1, d0, d1), replaced with
                # ModularIndexing(p0, d0, d1), it is not possible to match p0
                # with d0 * d1 since sympy is unaware of this fact. Precomputed
                # replacements are therefore removed prior to matching a
                # BlockPattern, and are reintroduced after any analysis that
                # works best on an expression with precomputed replacements removed
                sizevars = V.graph.sizevars
                index = sizevars.remove_precomputed_replacements(index)
                numel = sizevars.remove_precomputed_replacements(range_tree.numel)

                match_result = BlockPatternMatcher.match_mod_div_block_expr(
                    index, index_var, numel, num_dims
                )
                if match_result is None:
                    return None

                (
                    dims,
                    strides,
                    block_index_exprs,
                ) = match_result
                slice_numels = BlockPatternMatcher.get_slice_numels(dims)

                # Check for applicable iteration range sizes.
                # When mapping a 1D block into an ND one, we need to know that
                # the number of elements is not changed. This means the slice numels of
                # the ND iteration range must evenly divide the length of the 1D block.
                # There are two cases where we can guarantee this:
                #  1. Numels are powers of 2. If numel == 2 ** n, and we know XBLOCK == 2 ** m,
                #     with n and m integers, then either numel is a multiple of XBLOCK, or numel
                #     is less than XBLOCK. (If numel is less than XBLOCK, we round up to 1 below.)
                #  2. Numels are multiples of the maximum possible block size.
                sizevars = V.graph.sizevars
                max_block = self.max_block(range_tree.prefix)
                if any(
                    not sizevars.statically_known_multiple_of(numel, max_block)
                    and not sizevars.statically_known_power_of_2(numel)
                    for numel in slice_numels
                ):
                    return None

                # Compute the ND block shape from the linear block size.
                # Use CielDiv to round leading dimensions up to 1.
                # Non-leading dimensions are clamped to the size of the iteration range,
                # while the leading dimension can exceed this to accommodate a larger
                # block size.
                # See [Note: Precomputed replacements with BlockPatternMatch] for
                # the call to lookup_precomputed_size
                linear_block_size = TritonSymbols.get_block_size(range_tree)
                block_shape: list[sympy.Expr] = [
                    CeilDiv(
                        linear_block_size,
                        sizevars.lookup_precomputed_size(slice_numels[0]),
                    )
                ] + [
                    sympy.Min(
                        CeilDiv(
                            linear_block_size, sizevars.lookup_precomputed_size(numel)
                        ),
                        sizevars.lookup_precomputed_size(dim),
                    )
                    for numel, dim in zip(slice_numels[1:], dims[1:])
                ]

                # Compute block offsets from {xyzr}offset and the matched expressions.
                block_offsets: list[sympy.Expr] = [
                    sympy_subs(
                        expr, {index_var: TritonSymbols.get_block_offset(range_tree)}
                    )
                    for expr in block_index_exprs
                ]

                return BlockParameters(
                    shape=[sizevars.lookup_precomputed_size(d) for d in dims],
                    block_shape=block_shape,
                    strides=strides,
                    offsets=block_offsets,
                )

            def match_block_subexpr(
                expr: sympy.Expr,
                range_tree: IterationRangesRoot,
            ) -> BlockParameters | None:
                """
                Match a block indexing subexpression involving a single range tree.
                """
                for match_func in (
                    match_affine_block,
                    match_mod_div_block,
                ):
                    factored_index_expr = BlockPatternMatcher.factor_index_expr(
                        expr, range_tree.symbol()
                    )
                    match = match_func(factored_index_expr, range_tree)
                    if match is not None:
                        return match

                return None

            def match_block_expr() -> BlockDescriptorOptions | None:
                index_relative_to_xyr_index = sympy_subs(
                    index, {v: t.expr for v, t in self.range_tree_nodes.items()}
                )
                range_trees = self.active_range_trees()

                # Partition the index into subexpressions pertaining to each range tree.
                # For example xindex * 5 + r0_index * 3 is partitioned to
                # (xindex * 5, r0_index * 3).
                index_subexprs = [
                    BlockPatternMatcher.get_subexpr_involving_symbol(
                        index_relative_to_xyr_index, tree.symbol()
                    )
                    for tree in range_trees
                ]

                # Match each range tree's subexpression separately.
                range_symbols = OrderedSet(tree.symbol() for tree in range_trees)
                block_params = BlockParameters()
                for tree, subexpr in zip(range_trees, index_subexprs):
                    # Reject mixed terms, e.g. xindex * r0_index.
                    # NB: the zero expression is allowed, for broadcasting.
                    if len(range_symbols.intersection(subexpr.free_symbols)) > 1:
                        return None

                    # Match the subexpression for this range tree.
                    params = match_block_subexpr(subexpr, tree)
                    if params is None:
                        return None
                    block_params += params

                # Collect leftover terms as a constant offset.
                offset = index_relative_to_xyr_index - sum(index_subexprs)

                # Form the block pointer or TMA descriptor.
                self.filter_masks(mask_vars)

                options_class = (
                    self.block_ptr_options_cls
                    if config.triton.use_block_ptr
                    else self.tensor_descriptor_options_cls
                )
                nonlocal tma_compatibility_checker
                stride_sorter_cls: type[BlockParameters.StrideSorter]
                if config.triton.use_block_ptr:
                    can_lift = False
                    stride_sorter_cls = BlockParameters.IdentityStrideSorter
                else:
                    tma_compatibility_checker = cast(
                        TMACompatibilityChecker, tma_compatibility_checker
                    )
                    can_lift = tma_compatibility_checker.can_lift()

                    if (
                        self.transpose_discontiguous_tensor_descriptors_override
                        is not None
                    ):
                        transpose_contiguous = (
                            self.transpose_discontiguous_tensor_descriptors_override
                        )
                    else:
                        transpose_contiguous = (
                            config.triton.transpose_discontiguous_tensor_descriptor
                        )

                    # For templates:
                    # Only try transpose if we know the output shape
                    # in case we need to transpose the data.
                    if hasattr(self, "template_out_shape"):
                        transpose_contiguous &= copy_shape is not None

                    stride_sorter_cls = (
                        BlockParameters.TensorDecriptorStrideSorter
                        if transpose_contiguous
                        else BlockParameters.IdentityStrideSorter
                    )

                options = options_class.create(
                    params=block_params,
                    constant_offset=offset,
                    range_trees=range_trees,
                    mask_vars=mask_vars,
                    get_max_block=self.max_block,
                    can_lift=can_lift,
                    stride_sorter_cls=stride_sorter_cls,
                )
                if options_class == TensorDescriptorOptions:
                    tma_compatibility_checker = cast(
                        TMACompatibilityChecker, tma_compatibility_checker
                    )
                    if not tma_compatibility_checker.are_block_parameters_compatible(
                        options.params
                    ):
                        return None

                return options

            # Return a block pointer, if indexing matches the pattern.
            options = match_block_expr()
            if options is not None:
                return options
        expand_str = None
        expand_shape: BlockShapeType = None
        index_str = self.index_to_str(index)

        def _get_expand_str():
            if copy_shape:
                if isinstance(copy_shape, str):
                    return f"{copy_shape}.shape", None
                else:
                    return "[" + ", ".join(str(c) for c in copy_shape) + "]", copy_shape
            else:
                return self.dense_size_str(), tuple(self.dense_size_list())

        if is_sympy_integer_like(index):
            # Integer indexing produces a size-1 scalar tensor with the same shape
            # as the dense dimension. E.g, if dense_size = [YBLOCK, XBLOCK, R0_BLOCK],
            # then we create tl.full([1, 1, 1], int).
            #
            # Exceptions:
            # 1. If copy_shape is explicitly provided, use copy_shape expansion instead.
            # 2. If the dense tensor has only one dimension (e.g., [XBLOCK]),
            #    broadcasting does not apply. For example:
            #        tl.arange(0, XBLOCK) + tl.full([1], int)  # -> broadcasting error
            #    In this case, we fall back to dense indexing:
            #        tl.full([XBLOCK], int)
            if copy_shape or len(self.dense_size_list()) == 1:
                expand_str, expand_shape = _get_expand_str()
            else:
                expand_str = str([1] * len(self.dense_size_list()))
                expand_shape = tuple([1] * len(self.dense_size_list()))

            index_str = f"tl.full({expand_str}, {index_str}, tl.int32)"
            if self.fixed_config or self.is_combo_kernel or mask_constant_index:
                mask_vars = OrderedSet(
                    f"{tree.prefix}mask"
                    for tree in self.range_trees
                    if not tree.is_reduction and not self._has_constant_mask(tree)
                )
            else:
                mask_vars = OrderedSet()
            if self._load_mask:
                mask_vars.add(self._load_mask)
            return IndexingOptions(
                index_str,
                mask_vars,
                expand_str,
                has_rindex,
                index,
                expand_shape=expand_shape,
            )

        if need_dense and not have_dense:
            if self.inside_reduction and self.is_native_matmul:
                # This avoids full broadcasting (need_dense) when performing native matmul.
                # For example, self._load_mask previously required tl.broadcast_to() in index_str.
                # Due to the restrictions of tl.dot semantics, we only want to expand the block
                # shape for the necessary axes.
                #
                # Previously:
                #   tmp1 = tl.load(ptr + tl.broadcast_to(r0, [YBLOCK, XBLOCK, R0_BLOCK]),
                #                  r0_mask & tmp0 & xmask)
                #
                # Now:
                #   tmp1 = tl.load(ptr + tl.broadcast_to(r0, [1, 1, R0_BLOCK]),
                #                  r0_mask & tmp0 & xmask)
                #
                # We achieve this by determining the required block shape through mask inspection.
                # When a temporary variable appears in the mask (e.g., self._load_mask), we retrieve
                # its true shape by inspecting tmp.mask_vars tracked by TritonCSEVariable.
                #
                # Caution: it may miss the correct block shape if the specific mask was constant
                # and thus not tracked in TritonCSEVariable.mask_vars.
                #
                # TODO: Once the shape propagation PR lands, reimplement this logic:
                #       https://github.com/pytorch/pytorch/pull/152198
                mask_shape = mask_vars.copy()
                if self._load_mask:
                    mask_shape.add(self._load_mask)

                xyzr = OrderedSet(["xmask", "ymask", "zmask", "r0_mask"])
                while not mask_shape.issubset(xyzr):
                    tmp_masks = mask_shape.difference(xyzr)
                    tmp = tmp_masks.pop()
                    assert isinstance(tmp, TritonCSEVariable)
                    mask_shape.discard(tmp)
                    mask_shape.update(tmp.mask_vars)

                # e.g., expand_list becomes ['ZBLOCK', 1, 1, 'R0_BLOCK']
                expand_list = ["1"] * len(self.dense_size_list())
                for mask in mask_shape:
                    assert isinstance(mask, str)
                    for tree in self.active_range_trees():
                        if mask.startswith(tree.prefix):
                            dim = tree.tensor_dim
                            assert isinstance(dim, int)
                            expand_list[dim] = self.dense_size_list()[dim]

                expand_str = "[" + ",".join(map(str, expand_list)) + "]"
                expand_shape = tuple(expand_list)
                index_str = f"tl.broadcast_to({index_str}, {expand_str})"
            else:
                expand_str, expand_shape = _get_expand_str()
                index_str = f"tl.broadcast_to({index_str}, {expand_str})"
                mask_vars = dense_mask_vars
        elif not have_loop_vars and copy_shape:
            expand_shape_str, expand_shape = _get_expand_str()
            index_str = f"tl.broadcast_to({index_str}, {expand_shape_str})"
            mask_vars = dense_mask_vars

        if expand_shape is None:
            if need_dense or have_dense:
                _, expand_shape = _get_expand_str()
            else:
                expand_shape = ()

        if override_mask:
            mask_vars = OrderedSet([override_mask])

        if self._load_mask:
            mask_vars.add(self._load_mask)

        self.filter_masks(mask_vars)

        return IndexingOptions(
            index_str,
            mask_vars,
            expand_str,
            has_rindex,
            index,
            expand_shape=expand_shape,
        )