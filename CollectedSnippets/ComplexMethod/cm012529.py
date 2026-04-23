def _codegen_iteration_vars(
        self, kernel_body: IndentedBuffer, ctx: _CodegenContext
    ) -> None:
        # Generate iteration variables as jnp.arange arrays
        # Skip on GPU - jnp.arange is not supported by Pallas Mosaic backend
        if not (self.range_tree_nodes and not self.is_gpu and self.used_iter_vars):
            return

        kernel_body.writeline("# Define iteration variables as JAX arrays")

        reshape_target_shape, reshape_target_numel = (
            self._get_reshape_target_shape_and_numel()
        )

        var_items = list(self.range_tree_nodes.items())

        broadcast_vars = []
        total_var_idx = None
        for idx, (var_sym, entry) in enumerate(var_items):
            length_val = self._safe_int(entry.length)
            if length_val is not None and length_val == reshape_target_numel:
                total_var_idx = idx
            else:
                broadcast_vars.append(
                    _BroadcastedIterVar(idx, var_sym, entry, length_val)
                )

        num_broadcast_dims = len(broadcast_vars)

        for idx, (var_sym, entry) in enumerate(var_items):
            if var_sym not in self.used_iter_vars:
                continue
            var_name = str(var_sym)
            length = entry.length
            renamed_length = self.rename_indexing(length)
            length_str = self.kexpr(renamed_length)
            length_val = self._safe_int(length)

            if length_val is None:
                if (
                    reshape_target_shape
                    and num_broadcast_dims > 1
                    and idx != total_var_idx
                ):
                    broadcast_idx = next(
                        (i for i, v in enumerate(broadcast_vars) if v.idx == idx),
                        None,
                    )
                    if broadcast_idx is not None:
                        expr = self._make_broadcasted_iteration_var_expr(
                            broadcast_vars, broadcast_idx
                        )
                        kernel_body.writeline(f"{var_name} = {expr}")
                        continue
                kernel_body.writeline(f"{var_name} = jnp.arange({length_str})")
                continue

            if (
                reshape_target_shape
                and len(reshape_target_shape) > 1
                and length_val == reshape_target_numel
            ):
                shape_str = ", ".join(str(s) for s in reshape_target_shape)
                arange = f"jnp.arange({length_str})"
                kernel_body.writeline(f"{var_name} = {arange}.reshape({shape_str})")
            elif num_broadcast_dims > 1 and idx != total_var_idx:
                broadcast_idx = next(
                    i for i, v in enumerate(broadcast_vars) if v.idx == idx
                )
                expr = self._make_broadcasted_iteration_var_expr(
                    broadcast_vars, broadcast_idx
                )
                kernel_body.writeline(f"{var_name} = {expr}")
            else:
                # Simple 1D arange — emit tile-relative form so tiling is safe.
                # When grid=(1,), _pallas_tile[ax] == full length and
                # pl.program_id(0) == 0, so this degenerates to jnp.arange(N).
                # Only do this when the var actually appears in compute body
                # (otherwise tiling is not blocked and the full arange is fine).
                # Skip for scatter/index kernels where the iter var is used
                # as a global index, not a data value.
                compute_text = "\n".join(str(line) for line in self.compute._lines)
                var_in_compute = var_name in compute_text
                can_tile_relative = (
                    var_in_compute
                    and not self.is_gpu
                    and not self.outputs_need_read
                    and not self.has_flatten_indexing
                    and not entry.is_reduction
                )
                axis_idx = (
                    self._get_iter_var_axis(var_sym) if can_tile_relative else None
                )
                if axis_idx is not None:
                    kernel_body.writeline(
                        f"{var_name} = jnp.arange(_pallas_tile[{axis_idx}])"
                        f" + pl.program_id(_pallas_ax2g.get({axis_idx}, 0))"
                        f" * _pallas_tile[{axis_idx}]"
                    )
                    self.tile_relative_iter_vars.add(var_sym)
                else:
                    kernel_body.writeline(f"{var_name} = jnp.arange({length_str})")