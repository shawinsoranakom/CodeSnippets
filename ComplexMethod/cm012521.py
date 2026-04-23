def _build_scatter_store_expr(
        self,
        out: str,
        value: CSEVariable,
        scatter_info: dict[str, Any],
        name: str,
        mode: Any,
    ) -> str:
        """Build store expression for scatter operations (indirect indexing)."""
        is_point_scatter = scatter_info.get("is_point_scatter", False)

        # Mark this output parameter as needing to be readable (for aliasing)
        self.outputs_need_read.add(out)
        alias_param = f"{out}_alias"

        # Use .add() for atomic_add mode, .set() otherwise
        scatter_op = "add" if mode == "atomic_add" else "set"

        if is_point_scatter:
            # Single-element scatter
            indirect_var = scatter_info["indirect_var"]
            indirect_dim = scatter_info["indirect_dim"]
            output_shape = scatter_info["output_shape"]

            # Build index tuple with 0s for other dimensions
            index_parts = []
            for dim in range(len(output_shape)):
                if dim == indirect_dim:
                    index_parts.append(indirect_var)
                else:
                    index_parts.append("0")

            index_tuple = ", ".join(index_parts)
            return f"{out}[...] = {alias_param}[...].at[{index_tuple}].{scatter_op}({value})"

        # Scatter with iteration variables
        indirect_var = scatter_info["indirect_var"]
        dims_before = scatter_info["dims_before"]
        dims_after = scatter_info["dims_after"]

        # Determine if element-wise or slice-based scatter
        buf = V.graph.get_buffer(name)
        output_ndim = len(buf.get_size()) if buf is not None else 0

        num_iter_vars_in_store = len(dims_before) + len(dims_after)
        total_kernel_iter_vars = len(self.range_tree_nodes)
        remaining_dims = output_ndim - 1  # dims other than indirect

        is_element_wise = (
            num_iter_vars_in_store == remaining_dims
            and num_iter_vars_in_store == total_kernel_iter_vars
        )

        if is_element_wise:
            # Element-wise scatter: use iteration variable names
            index_parts = [var_name for var_name, size in dims_before]

            # Reshape indirect var for broadcasting if needed
            n_leading = len(dims_before)
            n_trailing = len(dims_after)
            if n_leading > 0 and n_trailing > 0:
                leading_ones = "None, " * n_leading
                trailing_nones = ", None" * n_trailing
                indirect_reshaped = f"{indirect_var}[{leading_ones}...{trailing_nones}]"
            else:
                indirect_reshaped = indirect_var
            index_parts.append(indirect_reshaped)

            index_parts.extend(var_name for var_name, size in dims_after)
        else:
            # Slice-based scatter: use : for iteration dimensions
            index_parts = [":" for _ in dims_before]
            index_parts.append(indirect_var)
            index_parts.extend(":" for _ in dims_after)

        index_tuple = ", ".join(index_parts)
        return (
            f"{out}[...] = {alias_param}[...].at[{index_tuple}].{scatter_op}({value})"
        )