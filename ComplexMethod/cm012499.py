def _convert_to_jax_slice(self, index: sympy.Expr) -> str:
        """
        Convert a sympy index expression to JAX slice notation.

        Handles common patterns like:
        - stride*var -> ::stride
        - stride*var + offset -> offset::stride

        For more complex patterns, falls back to explicit indexing.
        Uses BlockPatternMatcher for robust pattern matching.
        """
        # Get the iteration variables for this kernel
        if not self.range_trees:
            return "..."

        # Rename symbolic sizes to kernel parameter names upfront
        index = self.rename_indexing(index)

        # Check for ModularIndexing - this is NOT contiguous access
        # ModularIndexing is used for roll/wrap-around operations
        if index.has(ModularIndexing):
            # Track which iteration variables are used before returning
            self.used_iter_vars.update(self._get_used_iter_vars(index))
            # Generate actual index expression - iteration variables are already
            # defined as jnp.arange arrays, so we just convert to JAX code
            return self.kexpr(index)

        # Simplify the index
        index = V.graph.sizevars.simplify(index)
        # Find which iteration variable(s) are used
        used_vars = self._get_used_iter_vars(index)

        # Track which iteration variables are used
        self.used_iter_vars.update(used_vars)

        if len(used_vars) == 0:
            # No iteration variables, this is a constant index
            return str(index)
        elif len(used_vars) == 1:
            # Single iteration variable - try to extract stride and offset using BlockPatternMatcher
            var = next(iter(used_vars))

            # Get the subexpression involving this variable
            var_expr = BlockPatternMatcher.get_subexpr_involving_symbol(index, var)

            # Try to match affine pattern: stride * var
            stride = BlockPatternMatcher.match_affine_block_expr(var_expr, var)

            if stride is not None:
                offset = index - var_expr
                offset = V.graph.sizevars.simplify(offset)

                if stride < 0:
                    return self.kexpr(index)

                if offset == 0:
                    return "..."

                # Non-zero offset: check if we can use slice notation
                if stride != 1:
                    return self.kexpr(index)

                try:
                    offset_val = int(offset)
                    if offset_val < 0:
                        return self.kexpr(index)
                except (TypeError, ValueError):
                    return self.kexpr(index)

                return f"{self.kexpr(offset)}::1"
            else:
                # Couldn't match affine pattern, fall back to original logic
                offset = index - var_expr
                offset = V.graph.sizevars.simplify(offset)
                if offset == 0 and var_expr == var:
                    # Just the variable itself, unit stride
                    return "..."
        elif len(used_vars) > 1:
            # Multi-dimensional indexing
            # For contiguous multi-dim access, all terms should have unit stride
            all_unit_stride = True
            for var in used_vars:
                var_expr = BlockPatternMatcher.get_subexpr_involving_symbol(index, var)
                stride = BlockPatternMatcher.match_affine_block_expr(var_expr, var)
                if stride != 1:
                    all_unit_stride = False
                    break
            if all_unit_stride:
                # Contiguous multi-dimensional access
                return "..."
            else:
                # Strided multi-dimensional access
                # For most cases, inputs are made contiguous before passing to JAX,
                # so strided tensors become contiguous and we can use [...]
                # The buffer size check in load() handles im2col-like patterns
                return "..."

        # For complex cases, use [...] since inputs are made contiguous
        return "..."