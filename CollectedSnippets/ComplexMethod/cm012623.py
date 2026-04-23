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