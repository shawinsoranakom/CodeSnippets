def _build_load_expr(
        self,
        buf: str,
        name: str,
        index: sympy.Expr,
        indexing: _BufferIndexing,
    ) -> str:
        """
        Build the load expression based on indexing mode.
        """
        if indexing.needs_flatten:
            # Detect indirect (data-dependent) access for scalar prefetch
            indirect = self._detect_indirect_access(buf, name, index)
            if indirect is not None:
                if self.indirect_access is not None:
                    # Fused nodes may re-visit the same indirect load (e.g.
                    # a reduction + pointwise over the same embedding).
                    # Allow that, but reject truly different indirect accesses.
                    assert indirect == self.indirect_access, (
                        "only one indirect access per kernel supported"
                    )
                self.indirect_access = indirect
                return f"{buf}[0]"

            self.has_flatten_indexing = True
            self.flatten_indexed_buffers.add(name)
            # Flatten then index for non-contiguous access (gather operation)
            has_minmax = index.has(sympy.Min) or index.has(sympy.Max)
            idx_dtype = "jnp.int32" if self.is_tpu else "jnp.int64"
            idx = (
                f"({indexing.index_str}).astype({idx_dtype})"
                if has_minmax
                else indexing.index_str
            )
            return f"{buf}[...].flatten()[{idx}]"
        else:
            # Direct indexing for contiguous access
            load_expr = f"{buf}[{indexing.index_str}]"

            if indexing.index_str == "..." and not self.is_gpu:
                perm = self._get_full_load_permutation(name, index)
                if perm is not None:
                    load_expr = self._gather_permute_expr(load_expr, perm)
                    self.permuted_input_buffers[name] = perm
                else:
                    collapsed = self._get_collapsed_load_permutation(name, index)
                    if collapsed is not None:
                        collapsed_shape, cperm = collapsed
                        load_expr = f"jnp.permute_dims({load_expr}, {cperm})"
                        # Don't store cperm in permuted_input_buffers as it's for the reshaped tensor
                        # not the original shape, which causes issues later when used for tiling
                        self.collapsed_reshape_inputs[name] = collapsed_shape
                        self.collapsed_output_shape = tuple(
                            collapsed_shape[p] for p in cperm
                        )

            return load_expr