def _codegen_tiled_specs(self, ctx: _CodegenContext) -> None:
        """Generate tiled BlockSpec and grid variables for CPU/TPU.

        Tiles the last 1–2 dimensions of each tensor, respecting TPU
        alignment constraints (last dim multiple of 128, second-to-last
        multiple of 8).  Lower-ndim inputs are right-aligned with the
        reference output shape per numpy broadcast rules.
        """
        code = ctx.code
        skip_n = self.tile_skip_last_n
        has_transpose = "True" if self.tile_has_transpose else "False"
        is_tpu_literal = "True" if ctx.is_tpu else "False"

        # Collect per-input permutations for tiling alignment.
        all_perms: list[tuple[int, ...] | None] = []
        for p in ctx.kernel_input_params:
            buf_name = self._param_to_buf_name(p)
            all_perms.append(
                self.permuted_input_buffers.get(buf_name) if buf_name else None
            )

        mgp = self._cpu_max_grid_product
        mgp_arg = f", max_grid_product={mgp}" if mgp else ""
        perms_arg = (
            f", permutations={repr(all_perms)}"
            if any(p is not None for p in all_perms)
            else ""
        )
        code.writeline(
            f"_tile, _grid, _ax2g = pallas_compute_tiling("
            f"_pallas_out_shapes[0], "
            f"transpose={has_transpose}, "
            f"skip_last_n={skip_n}, exact_only=len(_pallas_out_shapes[0]) < 2, "
            f"is_tpu={is_tpu_literal}"
            f"{perms_arg}{mgp_arg})"
        )
        code.writeline("_ng = len(_grid)")
        code.writeline("_ref = _pallas_out_shapes[0]")

        code.writeline("out_specs_pallas = tuple(")
        code.writeline(
            "    pallas_make_block_spec(s, _ref, _tile, _ax2g, _ng, is_output=True)"
        )
        code.writeline("    for s in _pallas_out_shapes")
        code.writeline(")")

        self._codegen_strided_reshapes(code, ctx.kernel_input_params)

        # Reshape collapsed inputs before building specs.
        for param in ctx.kernel_input_params:
            buf_name = self._param_to_buf_name(param)
            cshape = self.collapsed_reshape_inputs.get(buf_name) if buf_name else None
            if cshape is not None:
                code.writeline(f"{param} = {param}.reshape({cshape})")

        # Build input BlockSpecs (with per-input permutation when needed).
        input_list = ", ".join(ctx.kernel_input_params)
        if any(p is not None for p in all_perms):
            perm_list = ", ".join(repr(p) for p in all_perms)
            code.writeline(f"_perm_flags = [{perm_list}]")
            code.writeline("in_specs_pallas = tuple(")
            code.writeline(
                f"    pallas_make_block_spec(i.shape, _ref, _tile, _ax2g, _ng, permutation=p)"
                f" for i, p in zip([{input_list}], _perm_flags)"
            )
            code.writeline(")")
        else:
            code.writeline("in_specs_pallas = tuple(")
            code.writeline(
                f"    pallas_make_block_spec(i.shape, _ref, _tile, _ax2g, _ng) for i in [{input_list}]"
            )
            code.writeline(")")