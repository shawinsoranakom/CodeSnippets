def _codegen_scalar_prefetch_wrapper(
        self,
        ctx: _CodegenContext,
        kernel_name: str,
        kernel_body: IndentedBuffer,
    ) -> None:
        """Emit kernel, JIT wrapper, and main entry for scalar prefetch."""
        assert self.indirect_access is not None
        indirect = self.indirect_access
        code = ctx.code

        alias_set = OrderedSet(ctx.alias_params)
        other_input_params = [
            p
            for p in ctx.kernel_input_params
            if p != indirect.indices_param
            and p != indirect.table_param
            and p not in alias_set
        ]

        # Emit kernel function with params reordered for PrefetchScalarGridSpec:
        # [scalar_prefetch] + [in_specs refs] + [out_specs refs]
        prefetch_kernel_params = (
            [indirect.indices_param]
            + [indirect.table_param]
            + other_input_params
            + list(ctx.alias_params)
            + ctx.output_params
        )
        code.writeline(
            f"def {kernel_name}_kernel({', '.join(prefetch_kernel_params)}):"
        )
        with code.indent():
            self._emit_kernel_body(code, kernel_body, ctx)

        # Emit JIT wrapper
        code.writeline("")
        jit_wrapper_name = f"{kernel_name}_jit_wrapper"
        wrapper_params = (
            ["out_shapes", "out_dtypes"] + ctx.size_var_params + ctx.kernel_input_params
        )
        static_argnums = list(range(2 + len(ctx.size_var_params)))
        static_argnums_literal = "(" + ", ".join(str(x) for x in static_argnums) + ",)"
        code.writeline(
            f"@functools.partial(jax.jit, static_argnums={static_argnums_literal})"
        )
        code.writeline(f"def {jit_wrapper_name}({', '.join(wrapper_params)}):")

        with code.indent():
            table = indirect.table_param
            indices = indirect.indices_param

            ind_dim = indirect.indirect_dim
            ndim = len(indirect.table_shape)
            code.writeline("_D = 1")
            for i in range(ndim):
                if i != ind_dim:
                    code.writeline(f"_D = _D * {table}.shape[{i}]")
            code.writeline(f"_seq = {indices}.shape[0]")

            if ind_dim == 0:
                code.writeline(f"_table_3d = {table}.reshape({table}.shape[0], 1, _D)")
            else:
                perm = (ind_dim, *[d for d in range(ndim) if d != ind_dim])
                code.writeline(
                    f"_table_3d = {table}.transpose{perm}.reshape("
                    f"{table}.shape[{ind_dim}], 1, _D)"
                )

            # Reshape other (non-table, non-indices) inputs to 3D to match the
            # table's (seq, 1, D) layout.  Currently handles:
            #   - 2D with leading dim == seq: row-aligned, reshape to (seq, 1, D)
            #   - 1D: broadcast scalar/vector, reshape to (1, 1, numel)
            #   - else: flatten to (1, 1, -1) — assumes broadcastable with
            #     (seq, 1, D).  This may not work correctly for 3D+ inputs.
            pallas_call_other_args = []
            for p in other_input_params:
                p3d = f"_{p}_3d"
                code.writeline(f"if {p}.ndim == 2 and {p}.shape[0] == _seq:")
                code.writeline(f"    {p3d} = {p}.reshape(_seq, 1, _D)")
                code.writeline(f"elif {p}.ndim == 1:")
                code.writeline(f"    {p3d} = {p}.reshape(1, 1, {p}.shape[0])")
                code.writeline("else:")
                code.writeline(f"    {p3d} = {p}.reshape(1, 1, -1)")
                pallas_call_other_args.append(p3d)

            pallas_call_alias_args = []
            for p in ctx.alias_params:
                p3d = f"_{p}_3d"
                code.writeline(f"{p3d} = {p}.reshape(_seq, 1, _D)")
                pallas_call_alias_args.append(p3d)

            partial_args = [f"{sv}={sv}" for sv in ctx.size_var_params]
            if partial_args:
                kernel_ref = (
                    f"functools.partial({kernel_name}_kernel,"
                    f" {', '.join(partial_args)})"
                )
            else:
                kernel_ref = f"{kernel_name}_kernel"

            # Reusable row-tiled BlockSpec (all i32 index_map for Mosaic compat)
            code.writeline(
                "_ROW_SPEC = pl.BlockSpec((1, 1, _D),"
                " lambda i, _: (i, jnp.int32(0), jnp.int32(0)))"
            )

            num_non_alias_in_specs = 1 + len(pallas_call_other_args)
            code.writeline("_in_specs = [")
            with code.indent():
                code.writeline(
                    "pl.BlockSpec((1, 1, _D),"
                    " lambda gi, idx: (idx[gi], jnp.int32(0), jnp.int32(0))),"
                )
                for p3d in pallas_call_other_args:
                    code.writeline(
                        f"_ROW_SPEC"
                        f" if {p3d}.shape[0] == _seq else"
                        f" pl.BlockSpec({p3d}.shape,"
                        f" lambda i, _: (jnp.int32(0), jnp.int32(0), jnp.int32(0))),"
                    )
                for _ in ctx.alias_params:
                    code.writeline("_ROW_SPEC,")
            code.writeline("]")

            num_outputs = len(ctx.output_params)
            code.writeline(
                "_out_specs = [" + ", ".join(["_ROW_SPEC"] * num_outputs) + "]"
            )

            # input_output_aliases: pallas_call arg index -> output index
            # (offset by 1 for scalar prefetch arg)
            alias_map_parts = []
            for out_idx, _ in enumerate(ctx.alias_params):
                arg_idx = 1 + num_non_alias_in_specs + out_idx
                alias_map_parts.append(f"{arg_idx}: {out_idx}")
            alias_map_literal = ", ".join(alias_map_parts)

            out_shape_parts = [
                f"jax.ShapeDtypeStruct((_seq, 1, _D), out_dtypes[{i}])"
                for i in range(num_outputs)
            ]
            out_shape_expr = "[" + ", ".join(out_shape_parts) + "]"

            code.writeline("_result = pl.pallas_call(")
            with code.indent():
                code.writeline(f"{kernel_ref},")
                code.writeline(f"out_shape={out_shape_expr},")
                code.writeline("grid_spec=pltpu.PrefetchScalarGridSpec(")
                with code.indent():
                    code.writeline("num_scalar_prefetch=1,")
                    code.writeline("grid=(_seq,),")
                    code.writeline("in_specs=_in_specs,")
                    code.writeline("out_specs=_out_specs,")
                code.writeline("),")
                if alias_map_parts:
                    code.writeline(f"input_output_aliases={{ {alias_map_literal} }},")
                if not self.is_tpu:
                    code.writeline(f"interpret={ctx.interpret_literal},")

            all_pallas_args = (
                [indices]
                + ["_table_3d"]
                + pallas_call_other_args
                + pallas_call_alias_args
            )
            code.writeline(f")({', '.join(all_pallas_args)})")

            code.writeline(
                "return tuple(r.reshape(s) for r, s in zip(_result, out_shapes))"
            )

        self._codegen_main_entry(ctx, jit_wrapper_name)