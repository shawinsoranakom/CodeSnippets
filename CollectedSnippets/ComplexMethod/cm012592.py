def are_block_parameters_compatible(
        self,
        block_params: BlockParameters,
    ) -> bool:
        """
        Check if the block parameters are valid for TMA.
        If force, we allow relying on symbolic hints equivalent
        to what we check for Triton templates.
        """
        if self.force:
            strides = [
                V.graph.sizevars.replace_backed_symbols_with_hints(st)
                for st in block_params.strides
            ]
        else:
            strides = block_params.strides

        # The TMA API requires that the innermost stride is 1
        # and that the outer strides are 16 byte aligned
        if not V.graph.sizevars.statically_known_equals(strides[-1], sympy.Integer(1)):
            log.debug(
                "%s TMA API requires innermost stride to be 1. Strides are: %s",
                self.failed_debug_prefix,
                strides,
            )
            return False

        element_size = self.dtype.itemsize
        for stride in strides[:-1]:
            if not V.graph.sizevars.statically_known_equals(
                ModularIndexing(stride * element_size, 1, sympy.Integer(16)),
                sympy.Integer(0),
            ):
                log.debug(
                    "%s TMA API requires outer strides to be 16 byte aligned. Dtype bytes: %d, strides: %s",
                    self.failed_debug_prefix,
                    element_size,
                    strides,
                )
                return False

        # Now compute the minimum value of the block type that is used
        # in the innermost block size that can guarantee that 16 bytes of data
        # can be loaded / stored.
        # Start with finding the innermost block type
        innermost_block_shape = block_params.block_shape[-1]

        # Pure singleton case
        if V.graph.sizevars.statically_known_equals(
            innermost_block_shape, sympy.Integer(1)
        ):
            log.debug(
                "%s innermost block shape cannot load 16 bytes. Block shape: %s",
                self.failed_debug_prefix,
                block_params.block_shape,
            )
            return False

        innermost_block_type = None
        innermost_block_symt = None
        for block_type_str in innermost_block_shape.free_symbols:
            for block_symt in TritonSymbols.block_types:
                if symbol_is_type(block_type_str, block_symt):
                    innermost_block_type = block_type_str
                    innermost_block_symt = block_symt
                    break

        assert innermost_block_type and innermost_block_symt, (
            f"{innermost_block_shape} expr must contain a single block type from {TritonSymbols.block_types}"
        )

        # For persistent reductions, the reduction block sizes are fixed at compile time.
        # Only apply this logic when the innermost block is a reduction block;
        # persistent reductions can still have pointwise-style loads where the innermost block is X/Y/Z,
        # and in that case we should fall back to the generic analysis below.
        if (
            self.kernel.persistent_reduction
            and not self.for_store
            and innermost_block_symt in TritonSymbols.reduction_types
        ):
            # For a discontiguous tensor, a 1D block will be split across several
            # dimensions, e.g. R0_BLOCK:
            # block_shape=[XBLOCK, ((R0_BLOCK + 31)//32), Min(1, ((R0_BLOCK + 31)//32)), Min(32, R0_BLOCK)]
            # The persistent R0_BLOCK will be a power of 2 that is at least r0_numel So it
            # should be guaranteed that Min(32, R0_BLOCK) * element_size >= 16
            innermost_tree_prefix = prefix_str[innermost_block_symt]
            tree_numel = None
            for t in self.kernel.range_trees:
                if t.is_reduction and t.prefix == innermost_tree_prefix:
                    tree_numel = t.numel
                    break
            if tree_numel is None:
                # If we can't map the innermost reduction block type to a reduction range tree,
                # we cannot determine the persistent RBLOCK value,
                # so we cannot validate the 16-byte innermost-dimension requirement for TMA.
                # Treat this as incompatible rather than asserting during compilation, fallback to non-TMA loads.
                log.debug(
                    "%s could not find reduction range tree for innermost prefix %s Block shape: %s",
                    self.failed_debug_prefix,
                    innermost_tree_prefix,
                    block_params.block_shape,
                )
                return False
            persistent_rblock = self.kernel._get_persistent_RBLOCK(tree_numel)
            innermost_block_bytes = (
                innermost_block_shape.subs({innermost_block_type: persistent_rblock})
                * element_size
            )
            if not V.graph.sizevars.statically_known_geq(
                innermost_block_bytes, sympy.Integer(16)
            ):
                log.debug(
                    "%s persistent reduction innermost block shape cannot load 16 bytes. Block shape: %s, persistent RBLOCK: %d",
                    self.failed_debug_prefix,
                    block_params.block_shape,
                    persistent_rblock,
                )
                return False

        else:
            # E.g. if the innermost block shape is Min(2, XBLOCK)
            # then the TMA API can only be used if the dtype has an 8 byte element
            # size so that 16 bytes of data can be loaded in the innermost dimension
            try:

                def indexing_div_rep(
                    x: sympy.Expr,
                    y: sympy.Expr,
                    z: sympy.Expr | None = None,
                ) -> sympy.Expr:
                    div = x / y
                    if z:
                        div = div % z
                    return div

                solve_expr = innermost_block_shape * element_size - 16
                # Sympy cannot handle FloorDiv and ModularIndexing well, so simplify
                solve_expr_simplified = solve_expr.replace(
                    FloorDiv, indexing_div_rep
                ).replace(ModularIndexing, indexing_div_rep)
                min_block_size = next_power_of_2(
                    int(
                        sympy.nsolve(
                            solve_expr_simplified,
                            innermost_block_type,
                            1,
                        )
                    )
                )

                # TODO: min block size may be too large / introduce redundancy
                if min_block_size > self.kernel.max_block(
                    prefix_str[innermost_block_symt]
                ):
                    log.debug(
                        "%s the minimum block size to satisfy expression %s is too large: %d",
                        self.failed_debug_prefix,
                        solve_expr_simplified,
                        min_block_size,
                    )
                    return False

                block_type_str = self.kernel.index_to_str(innermost_block_type)
                # Check block sizes if the user has provided a fixed triton config
                if self.kernel.fixed_config:
                    if min_block_size > self.kernel.fixed_config[block_type_str]:
                        log.debug(
                            "%s For block %s, fixed config block size %d is smaller "
                            "than the minimum required: %d",
                            self.failed_debug_prefix,
                            block_type_str,
                            self.kernel.fixed_config[block_type_str],
                            min_block_size,
                        )
                        return False
                else:
                    # Update the minimum block sizes that are passed to triton
                    # heuristics
                    self.kernel.tma_min_block_sizes[block_type_str] = max(
                        min_block_size,
                        self.kernel.tma_min_block_sizes.get(block_type_str, 1),
                    )

            except ValueError:
                log.debug(
                    "%s innermost block shape cannot load 16 bytes. Block params: %s",
                    self.failed_debug_prefix,
                    block_params.block_shape,
                )
                return False

        return True