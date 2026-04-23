def _get_full_load_permutation(
        self, name: str, index: sympy.Expr
    ) -> tuple[int, ...] | None:
        """Return permutation for a full-array load, or None.

        Computes the permutation by mapping each range-tree variable to
        both an output dimension (via store coefficients + actual output
        strides) and an input dimension (via load coefficients + input
        C-contiguous strides).  The permutation is then:

            perm[out_dim] = in_dim   for each RT variable

        Using actual output strides (not C-contiguous) is critical: the
        scheduler may choose a non-standard output layout (e.g. column-
        major) to optimise for transposed inputs.

        When all dimensions collapse to a single flat RT variable (e.g.
        (2,2,2,2,2) with all dims size 2), infers the permutation
        directly from output strides vs input C-contiguous strides.
        """
        info = self._get_buffer_info(name)
        if not info:
            return None
        _, buf_size, _, _, is_contiguous = info
        in_shape_raw = [self._safe_int(s) for s in buf_size]
        if len(in_shape_raw) < 2 or None in in_shape_raw:
            return None
        in_shape: list[int] = cast(list[int], in_shape_raw)
        if not is_contiguous:
            return None  # .contiguous() at JAX boundary handles this

        # Extract index coefficients for each non-reduction RT variable.
        iter_used = self._get_used_iter_vars(index)
        ordered = [
            s
            for s, e in self.range_tree_nodes.items()
            if s in iter_used and not e.is_reduction
        ]
        if len(ordered) != len(in_shape):
            # All dims may have collapsed to a single flat RT variable
            # (e.g. (2,2,2,2,2) → single x0 of length 32).  In this
            # case, infer the permutation directly from output strides
            # vs input C-contiguous strides.
            n = len(in_shape)
            if len(ordered) == 1 and self._safe_int(
                self.range_tree_nodes[ordered[0]].length
            ) == math.prod(in_shape):
                in_strides = self._c_contiguous_strides(in_shape)
                for out_name in self._output_buffer_names:
                    out_buf = V.graph.get_buffer(out_name)
                    if out_buf is None:
                        continue
                    out_shape = [self._safe_int(s) for s in out_buf.get_size()]
                    if any(s is None for s in out_shape) or len(out_shape) != n:
                        continue
                    actual = self._get_actual_out_strides(out_buf, n)
                    if actual is None:
                        break
                    # Map each output dim to the input dim with the
                    # same stride.
                    perm = self._map_coeffs_to_dims(actual, in_strides)
                    if perm is None:
                        break
                    if list(perm) == list(range(n)):
                        return None
                    return tuple(perm)
            return None
        coeffs_raw = [
            self._get_index_coefficient(V.graph.sizevars.simplify(index), v)
            for v in ordered
        ]
        if not all(isinstance(c, int) and c > 0 for c in coeffs_raw):
            return None
        coeffs: list[int] = cast(list[int], coeffs_raw)

        n = len(ordered)
        in_strides = self._c_contiguous_strides(in_shape)
        store_coeffs = self._compute_store_coeffs(ordered)

        # --- Primary path: dimension-mapping with actual output strides ---
        if store_coeffs is not None:
            for out_name in self._output_buffer_names:
                out_buf = V.graph.get_buffer(out_name)
                if out_buf is None:
                    continue
                out_shape = [self._safe_int(s) for s in out_buf.get_size()]
                if any(s is None for s in out_shape) or len(out_shape) != n:
                    continue

                actual = self._get_actual_out_strides(out_buf, n)
                if actual is not None:
                    rt_to_out = self._map_coeffs_to_dims(
                        [store_coeffs[v] for v in ordered], actual
                    )
                    rt_to_in = self._map_coeffs_to_dims(list(coeffs), in_strides)
                    if rt_to_out is not None and rt_to_in is not None:
                        perm = [0] * n
                        for k in range(n):
                            perm[rt_to_out[k]] = rt_to_in[k]
                        if list(perm) == list(range(n)):
                            return None
                        return tuple(perm)
                break

        return None