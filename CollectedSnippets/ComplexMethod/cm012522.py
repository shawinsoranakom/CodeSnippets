def _handle_mixed_indexing(self, index: sympy.Expr) -> str:
        """
        Handle indexing with both indirect variables and iteration variables.

        For example, x[indices, :] generates index = i0 + stride * tmp0
        where tmp0 is loaded from indices and i0 is the iteration variable.

        We need to convert this to JAX advanced indexing with proper broadcasting.
        When there are multiple iteration variables, they need different shapes
        to form an outer product (grid) rather than broadcasting together.

        Special case: For gather operations where a single iteration variable
        and single indirect variable have the same extent, they should be
        element-wise aligned, not broadcast into an outer product.

        PyTorch advanced indexing semantics: When multiple indirect indices have
        the same shape, they are paired element-wise (not outer product), and
        the combined result dimension appears at the FRONT of the output.
        """
        used_iter_vars_set = self._get_used_iter_vars(index)

        # Track which iteration variables are used
        self.used_iter_vars.update(used_iter_vars_set)

        if len(used_iter_vars_set) == 0:
            return self.kexpr(index)

        # Sort iteration variables by their coefficient (stride) in the index expression.
        # Variables with larger strides correspond to earlier output dimensions.
        # Use inf default so symbolic coefficients sort as outermost dimensions.
        def _coeff(var):
            return self._get_index_coefficient(index, var, default=float("inf"))

        used_iter_vars = sorted(used_iter_vars_set, key=_coeff, reverse=True)
        iter_coeffs = [_coeff(var) for var in used_iter_vars]

        # Rename symbolic sizes to kernel parameter names
        index_str = self.kexpr(self.rename_indexing(index))
        indirect_var_syms = self._get_indirect_vars(index)
        indirect_vars = [str(sym) for sym in indirect_var_syms]

        # Get coefficients for indirect vars to determine output ordering
        indirect_coeffs = {str(s): _coeff(s) for s in indirect_var_syms}

        # Special case: reduction var + single indirect var = element-wise gather
        # Reduction vars (r prefix) iterate over the reduction dimension, and when paired
        # with an indirect var, both are aligned to that dimension (element-wise).
        # Pointwise vars form output dimensions and need the complex reshape code.
        if len(used_iter_vars) == 1 and len(indirect_vars) == 1:
            var = used_iter_vars[0]
            var_name = str(var)
            is_reduction_var = (
                var in self.range_tree_nodes and self.range_tree_nodes[var].is_reduction
            )

            if is_reduction_var:
                # Reduction var: simple element-wise gather
                if var in self.range_tree_nodes:
                    range_entry = self.range_tree_nodes[var]
                    range_size = range_entry.length
                    # Rename to use kernel parameter names for symbolic sizes
                    renamed_size = self.rename_indexing(range_size)
                    arange_expr = f"jnp.arange({self.kexpr(renamed_size)})"
                    index_str = index_str.replace(var_name, arange_expr)
                return index_str
            # For pointwise vars, fall through to the complex reshape code

        # Check if multiple indirect vars should be paired element-wise.
        # In PyTorch, when multiple advanced indices have the same shape, they pair up.
        # The paired dimension goes to the FRONT of the output.
        # However, if indirect vars have different shapes (e.g., (1,4) and (4,1)),
        # they form an outer product instead.
        # We detect element-wise pairing when:
        # 1. Multiple indirect vars exist
        # 2. There's exactly ONE unused iteration variable (for the shared paired dim)
        # For outer product, there are MULTIPLE unused iter vars (one per indirect dim)
        paired_indirect = False
        if len(indirect_vars) > 1:
            # Count unused iteration variables (defined but not in index expression)
            unused_iter_vars = self._get_iter_vars() - used_iter_vars_set
            # Element-wise pairing: one unused iter var for the shared paired dimension
            # Outer product: multiple unused iter vars (one for each indirect var dimension)
            paired_indirect = len(unused_iter_vars) == 1

        if paired_indirect:
            # Multiple indirect vars with element-wise pairing
            # Output order: (paired_indirect_dim, iter_var_dims...)
            # All indirect vars get the same shape: (N, 1, 1, ...) for first dim
            # Iter vars come after: second dim onwards

            # Count total output dims: 1 (paired) + len(iter_vars) for non-newaxis
            # But some iter vars may be for newaxis dimensions (size 1)
            n_output_dims = 1 + len(used_iter_vars)

            # Reshape indirect vars to occupy the first dimension
            for indirect_var in indirect_vars:
                trailing_ones = ", 1" * len(used_iter_vars)
                reshape_expr = f"{indirect_var}.reshape(-1{trailing_ones})"
                index_str = index_str.replace(indirect_var, reshape_expr)

            # Reshape iteration variables to occupy subsequent dimensions
            # Sort by coefficient (descending) to determine order
            for i, var in enumerate(used_iter_vars):
                var_name = str(var)
                if var in self.range_tree_nodes:
                    range_entry = self.range_tree_nodes[var]
                    range_size = range_entry.length
                    # Rename to use kernel parameter names for symbolic sizes
                    renamed_size = self.rename_indexing(range_size)

                    # Shape: (1, ..., N, ..., 1) where N is at position i+1
                    # Position 0 is for paired indirect vars
                    shape_parts = ["1"] * n_output_dims
                    shape_parts[i + 1] = self.kexpr(renamed_size)
                    shape_str = ", ".join(shape_parts)
                    arange_expr = (
                        f"jnp.arange({self.kexpr(renamed_size)}).reshape({shape_str})"
                    )

                    index_str = index_str.replace(var_name, arange_expr)

            return index_str

        # Single indirect var case (or no indirect vars handled above)
        # Build a sorted list of all components by coefficient (descending)
        # Each component is (coeff, type, var) where type is 'iter' or 'indirect'
        all_components = []
        for var in used_iter_vars:
            all_components.append((_coeff(var), "iter", var))
        for sym in indirect_var_syms:
            all_components.append((_coeff(sym), "indirect", sym))
        all_components.sort(key=lambda x: x[0], reverse=True)

        # Calculate trailing dims needed for each component
        # Each component needs trailing dims for all subsequent iter vars
        # plus trailing dims for all dimensions of subsequent indirect vars
        # For simplicity, assume each indirect var contributes some dimensions
        # that will be handled by the reshape at store time

        # For iter vars, we need to count how many dimensions come after in the output
        for i, var in enumerate(used_iter_vars):
            var_name = str(var)
            if var in self.range_tree_nodes:
                range_entry = self.range_tree_nodes[var]
                range_size = range_entry.length
                # Rename to use kernel parameter names for symbolic sizes
                renamed_size = self.rename_indexing(range_size)
                var_coeff = _coeff(var)

                arange_expr = f"jnp.arange({self.kexpr(renamed_size)})"

                # Count trailing dims needed:
                # - One for each subsequent iter var (with smaller coeff)
                # - One for each dimension of indirect vars with smaller coeff
                # For indirect vars, assume each contributes 2 dims (common case)
                # The actual reshape at store time will fix any shape mismatches
                n_trailing_iter = sum(1 for c in iter_coeffs if c < var_coeff)
                n_trailing_indirect = sum(
                    2 for c in indirect_coeffs.values() if c < var_coeff
                )
                n_trailing = n_trailing_iter + n_trailing_indirect

                if n_trailing > 0:
                    trailing_dims = ", None" * n_trailing
                    arange_expr = f"{arange_expr}[:{trailing_dims}]"

                index_str = index_str.replace(var_name, arange_expr)

        # Reshape indirect variables for proper broadcasting.
        for indirect_var in indirect_vars:
            indirect_coeff = indirect_coeffs[indirect_var]

            # Count dims needed before and after this indirect var
            n_leading = sum(1 for c in iter_coeffs if c > indirect_coeff)
            n_trailing = sum(1 for c in iter_coeffs if c < indirect_coeff)

            # Build the indexing expression with leading Nones, ellipsis, trailing Nones
            if n_leading > 0 and n_trailing > 0:
                leading_nones = "None, " * n_leading
                trailing_nones = ", None" * n_trailing
                reshape_expr = f"{indirect_var}[{leading_nones}...{trailing_nones}]"
            elif n_leading > 0:
                leading_nones = "None, " * n_leading
                reshape_expr = f"{indirect_var}[{leading_nones}...]"
            elif n_trailing > 0:
                trailing_nones = ", None" * n_trailing
                reshape_expr = f"{indirect_var}[...{trailing_nones}]"
            else:
                reshape_expr = indirect_var

            index_str = index_str.replace(indirect_var, reshape_expr)

        return index_str