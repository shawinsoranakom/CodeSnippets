def store(
        self, name: str, index: sympy.Expr, value: CSEVariable, mode: Any = None
    ) -> None:
        # mode can be None (set), "atomic_add" (accumulate), etc.
        if mode is not None and mode != "atomic_add":
            raise Unsupported(f"pallas store mode '{mode}' not supported")
        out = self.args.output(name)
        self.store_buffer_names.add(name)

        # Check if this is a scalar output (reduction to scalar)
        buf = V.graph.get_buffer(name)
        is_scalar = buf is not None and len(buf.get_size()) == 0

        if is_scalar:
            store_lines = [
                f"_val = jnp.asarray({value})",
                f"{out}[...] = jnp.full({out}.shape, _val) if _val.ndim == 0 else _val.reshape({out}.shape)",
            ]
        else:
            # When collapsed_output_shape is set, the load-side permutation
            # already produces data in the correct layout for the collapsed
            # output.  Force a full-array store ("...") so the scatter index
            # (which was computed for the original output layout) does not
            # rearrange the permuted data.
            if self.collapsed_output_shape is not None:
                store_lines = self._build_full_array_store_expr(out, value, False)
            else:
                # Check for scatter pattern (indirect indexing for stores)
                scatter_info = self._detect_scatter_pattern(index, name)

                if scatter_info is not None:
                    # Track iteration variables used in scatter index
                    self.used_iter_vars.update(self._get_used_iter_vars(index))
                    store_lines = [
                        self._build_scatter_store_expr(
                            out, value, scatter_info, name, mode
                        )
                    ]
                else:
                    # Get base index expression
                    indexing = self._get_index_expr(index)

                    # Check for im2col-like patterns
                    indexing = self._check_im2col_pattern(index, indexing)

                    # Build the store expression
                    store_lines = self._build_store_expr(
                        out, name, index, value, indexing, mode
                    )

        for line in store_lines:
            self.stores.writeline(line)
            # Track which output param this store uses for filtering in codegen_kernel
            self.store_with_output.append((out, line))