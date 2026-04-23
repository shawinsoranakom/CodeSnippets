def compute_boundary_check(
        self,
        get_max_block: Callable[[str], int],
        range_trees: list[IterationRangesRoot],
    ) -> None:
        """List of indices to pass to tl.load(boundary_check=...)"""
        sizevars = V.graph.sizevars

        # Substitute maximum block sizes in shape expressions.
        # This works in multiple_of checks because block sizes are powers of 2.
        block_to_max: dict[sympy.Expr, Any] = {
            TritonSymbols.block_sizes[t.symt]: get_max_block(prefix_str[t.symt])
            for t in range_trees
        }

        # Also see Note: Constant mask optimisation
        # if ynumel / YBLOCK > max_ygrid, then the z dimension is used to handle
        # the remaining programs that cannot fit into the y dimension. This means
        # it's possible that more than the required number of programs are launched,
        # possibly leading to out-of-bounds accesses. So even if ynumel divides YBLOCK,
        # boundary checking is required in the dimensions that are based on YBLOCK
        # e.g. for [YBLOCK // 16, YBLOCK, XBLOCK] dimensions 0 and 1 need boundary
        # checks when max_ygrid is exceeded.
        needs_overflow_grid = any(map(V.kernel.needs_yz_grid_overflow, range_trees))
        self._boundary_check = [
            idx
            for idx in range(len(self.shape))
            if (
                not sizevars.statically_known_equals(self.strides[idx], sympy.S.Zero)
                and (
                    (
                        needs_overflow_grid
                        and TritonSymbols.block_sizes[SymT.YBLOCK]
                        in self.block_shape[idx].free_symbols
                    )
                    or (
                        not sizevars.statically_known_multiple_of(
                            self.shape[idx], self.block_shape[idx]
                        )
                        and not sizevars.statically_known_multiple_of(
                            self.shape[idx],
                            sympy_subs(self.block_shape[idx], block_to_max),
                        )
                    )
                )
                and not (
                    V.kernel.no_x_dim
                    and self.block_shape[idx] == TritonSymbols.block_sizes[SymT.XBLOCK]
                )
            )
        ]