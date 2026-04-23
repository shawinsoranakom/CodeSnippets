def _build_store_expr(
        self,
        out: str,
        name: str,
        index: sympy.Expr,
        value: CSEVariable,
        indexing: _BufferIndexing,
        mode: Any = None,
    ) -> list[str]:
        """
        Build the store expression based on indexing mode.
        mode can be None (set) or "atomic_add" (accumulate).
        Returns a list of lines to emit.
        """
        if indexing.index_str == "...":
            # Full array store with shape matching
            needs_transpose = self._check_store_needs_transpose(name)
            return self._build_full_array_store_expr(out, value, needs_transpose)

        if indexing.needs_flatten:
            self.has_flatten_indexing = True
            # Block variable indexing (e.g., im2col) - use flattened scatter
            scatter_op = "add" if mode == "atomic_add" else "set"
            return [
                f"{out}[...] = {out}[...].flatten().at[({indexing.index_str}).flatten()].{scatter_op}("
                f"jnp.asarray({value}).flatten()).reshape({out}.shape)"
            ]

        # Direct indexed assignment
        has_indirect = self._has_indirect_vars(index)
        buf = V.graph.get_buffer(name)

        if buf is not None:
            buf_size = buf.get_size()
            if len(buf_size) > 1 and not self._has_iteration_vars(index):
                # Multi-dim output with constant index - use [...] for full assignment
                return self._build_full_array_store_expr(out, value, False)

        if has_indirect:
            # Indirect indexed store (scatter): use .add() for atomic_add, .set() otherwise
            scatter_op = "add" if mode == "atomic_add" else "set"
            lines = [f"_val = jnp.asarray({value})"]
            value_expr = f"(jnp.full({indexing.index_str}.shape, _val) if _val.ndim == 0 else {value})"
            if mode == "atomic_add":
                # For atomic_add, mark output as needing to be readable (for aliasing)
                self.outputs_need_read.add(out)
                alias_param = f"{out}_alias"
                lines.append(
                    f"{out}[...] = {alias_param}[...].flatten().at[({indexing.index_str}).flatten()].{scatter_op}("
                    f"{value_expr}.flatten()).reshape({out}.shape)"
                )
            else:
                lines.append(f"{out}[{indexing.index_str}] = {value_expr}")
            return lines

        return [f"{out}[{indexing.index_str}] = {value}"]