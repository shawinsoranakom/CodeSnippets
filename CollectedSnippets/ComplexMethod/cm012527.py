def codegen_kernel(self, name: str | None = None) -> str:  # type: ignore[override]
        """
        Generate the complete Pallas kernel code as a Python string.

        This includes:
        - Import statements for JAX/Pallas
        - The kernel function that operates on refs
        - The main wrapper function that handles PyTorch<->JAX conversions via DLPack

        Args:
            name: Optional kernel name (will use placeholder if not provided)

        Returns:
            str: Complete Python source code for the Pallas kernel
        """
        code = IndentedBuffer()

        # Define the Pallas kernel: accepts refs, uses broadcasted expressions
        arg_defs, call_args, _, _ = self.args.python_argdefs()
        kernel_params = [a.name for a in arg_defs]
        pure_out_params = [p for p in kernel_params if p.startswith("out_ptr")]
        output_params = [
            p for p in kernel_params if p.startswith(("out_ptr", "in_out_ptr"))
        ]
        # Identify size variable parameters (scalars like load_seed_offset)
        size_var_names = OrderedSet(self.args.sizevars.values())
        size_var_params = [p for p in kernel_params if p in size_var_names]
        if not output_params:
            raise RuntimeError("Pallas backend requires at least one output buffer")

        output_buffer_lookup = {
            inner: outer
            for outer, inner in self.args.output_buffers.items()
            if isinstance(inner, str)
        }

        kernel_name = name or "<KERNEL_NAME>"
        interpret_is_cpu = V.graph.get_current_device_or_throw().type == "cpu"
        interpret_literal = "True" if interpret_is_cpu else "False"

        aliasable_flags: dict[str, bool] = {}
        for param in pure_out_params:
            aliasable_flags[param] = True
        alias_params = [
            f"{param}_alias" for param in pure_out_params if aliasable_flags[param]
        ]
        pointer_tail = [
            p for p in kernel_params if p.startswith(("in_out_ptr", "in_ptr"))
        ]
        kernel_input_params = alias_params + pointer_tail
        full_kernel_params = alias_params + kernel_params
        non_alias_out_set = OrderedSet(
            [name for name, flag in aliasable_flags.items() if not flag]
        )
        # On CPU (interpret=True), pallas_call returns new arrays so we must
        # copy back every output.  On TPU, call_custom_kernel with
        # input_output_aliases handles donation (zero-copy), so no copy is
        # needed.  On CUDA, aliased outputs are mutated in-place by the
        # donated-buffer mechanism so only non-aliased outputs need a copy.
        if interpret_is_cpu:
            copy_output_indices = list(range(len(output_params)))
        elif self.is_tpu:
            copy_output_indices = []
        else:
            copy_output_indices = [
                idx
                for idx, name in enumerate(output_params)
                if name in non_alias_out_set
            ]

        ctx = _CodegenContext(
            code=code,
            kernel_name=kernel_name,
            is_tpu=self.is_tpu,
            interpret_is_cpu=interpret_is_cpu,
            interpret_literal=interpret_literal,
            kernel_params=kernel_params,
            pure_out_params=pure_out_params,
            output_params=output_params,
            size_var_params=size_var_params,
            output_buffer_lookup=output_buffer_lookup,
            aliasable_flags=aliasable_flags,
            alias_params=alias_params,
            pointer_tail=pointer_tail,
            kernel_input_params=kernel_input_params,
            full_kernel_params=full_kernel_params,
            non_alias_out_set=non_alias_out_set,
            copy_output_indices=copy_output_indices,
            alias_pairs=[],
        )
        self.aliasable_out_ptrs = aliasable_flags

        self._codegen_imports(ctx)

        kernel_body = IndentedBuffer()
        with kernel_body.indent():
            self._codegen_iteration_vars(kernel_body, ctx)

            for line in self.compute._lines:
                kernel_body.writeline(str(line))

        # Recompute kernel parameters after kernel body generation.
        # Size variables may have been registered during kernel body generation
        # (e.g., via rename_indexing for symbolic sizes), so we need to re-fetch
        # the arg defs to capture all parameters including newly-registered size vars.
        arg_defs, call_args, _, _ = self.args.python_argdefs()
        kernel_params = [a.name for a in arg_defs]
        size_var_names = OrderedSet(self.args.sizevars.values())
        ctx.size_var_params = [p for p in kernel_params if p in size_var_names]
        ctx.pointer_tail = [
            p for p in kernel_params if p.startswith(("in_out_ptr", "in_ptr"))
        ]
        ctx.kernel_input_params = alias_params + ctx.pointer_tail
        ctx.full_kernel_params = alias_params + kernel_params

        # Decide whether to use tiling for CPU/TPU after kernel body is fully
        # generated (used_iter_vars is populated during load/store codegen).
        self.tile_cpu_tpu = self._can_tile_cpu_tpu()

        extra_kernel_params = ""
        if self.tile_relative_iter_vars:
            extra_kernel_params = ", _pallas_tile=None, _pallas_ax2g=None"

        ctx.alias_pairs = self._compute_alias_pairs(ctx, aliasable_flags)

        use_scalar_prefetch = bool(self.indirect_access)

        if use_scalar_prefetch:
            self._eliminate_dead_indirect_code()
            kernel_body_sp = IndentedBuffer()
            with kernel_body_sp.indent():
                for line in self.compute._lines:
                    kernel_body_sp.writeline(str(line))
            self._codegen_scalar_prefetch_wrapper(
                ctx,
                kernel_name,
                kernel_body_sp,
            )
            return code.getvalue()

        # Emit the kernel function with the correct signature
        kernel_signature = f"def {kernel_name}_kernel({', '.join(ctx.full_kernel_params)}{extra_kernel_params}):"
        code.writeline(kernel_signature)

        with code.indent():
            self._emit_kernel_body(code, kernel_body, ctx)

        code.writeline("")
        jit_wrapper_name = f"{kernel_name}_jit_wrapper"
        donate_indices = []
        base_offset = 2 + len(ctx.size_var_params)
        for idx, name in enumerate(ctx.kernel_input_params):
            if (name in alias_params) or name.startswith("in_out_ptr"):
                donate_indices.append(idx + base_offset)
        if donate_indices:
            donate_literal = "(" + ", ".join(str(x) for x in donate_indices) + ",)"
        else:
            donate_literal = "()"
        static_argnums = list(range(2 + len(ctx.size_var_params)))
        static_argnums_literal = "(" + ", ".join(str(x) for x in static_argnums) + ",)"
        code.writeline(
            "@functools.partial("
            f"jax.jit, static_argnums={static_argnums_literal}, donate_argnums="
            f"{donate_literal})"
        )
        wrapper_params = (
            ["out_shapes", "out_dtypes"] + ctx.size_var_params + ctx.kernel_input_params
        )
        code.writeline(f"def {jit_wrapper_name}({', '.join(wrapper_params)}):")

        alias_map_literal = ", ".join(f"{i}: {o}" for (i, o) in ctx.alias_pairs)

        has_zero_dim, has_unknown_dim = self._zero_dim_output_flags(ctx)

        zero_dim_return = (
            "results = tuple(jnp.empty(s, dtype=dt) "
            "for s, dt in zip(out_shapes, out_dtypes))",
            "return results if len(results) > 1 else results[0]",
        )

        with code.indent():
            if has_zero_dim:
                code.writelines(zero_dim_return)
            else:
                if has_unknown_dim:
                    code.writeline("if any(0 in shape for shape in out_shapes):")
                    with code.indent():
                        code.writelines(zero_dim_return)
                # Pallas requires >= 1-d tensors; promote 0-d to (1,)
                code.writeline(
                    "_pallas_out_shapes = tuple("
                    "s if len(s) > 0 else (1,) for s in out_shapes)"
                )
                if self.collapsed_output_shape is not None:
                    code.writeline(
                        f"_pallas_out_shapes = ({self.collapsed_output_shape},)"
                    )
                # Reshape aliased inputs to match promoted output shapes
                for input_idx, out_idx in ctx.alias_pairs:
                    param = ctx.kernel_input_params[input_idx]
                    code.writeline(
                        f"{param} = {param}.reshape(_pallas_out_shapes[{out_idx}])"
                    )
                code.writeline("out_shapes_pallas = tuple(")
                code.writeline("    jax.ShapeDtypeStruct(shape, dtype)")
                code.writeline(
                    "    for shape, dtype in zip(_pallas_out_shapes, out_dtypes)"
                )
                code.writeline(")")
                if self.tile_cpu_tpu:
                    self._codegen_tiled_specs(ctx)
                else:
                    self._codegen_strided_reshapes(code, ctx.kernel_input_params)
                    for param in ctx.kernel_input_params:
                        buf_name = self._param_to_buf_name(param)
                        cshape = (
                            self.collapsed_reshape_inputs.get(buf_name)
                            if buf_name
                            else None
                        )
                        if cshape is not None:
                            code.writeline(f"{param} = {param}.reshape({cshape})")

                    code.writeline("out_specs_pallas = tuple(")
                    code.writeline("    pallas_make_block_spec_non_tiled(shape)")
                    code.writeline(
                        "    for shape, dtype in zip(_pallas_out_shapes, out_dtypes)"
                    )
                    code.writeline(")")
                    code.writeline("in_specs_pallas = tuple(")
                    code.writeline("    pallas_make_block_spec_non_tiled(i.shape)")
                    code.writeline(
                        "    for i in [" + ", ".join(ctx.kernel_input_params) + "]"
                    )
                    code.writeline(")")

                if self.tile_relative_iter_vars:
                    if self.tile_cpu_tpu:
                        code.writeline("_pallas_tile = _tile")
                        code.writeline("_pallas_ax2g = _ax2g")
                    else:
                        code.writeline("_pallas_tile = _pallas_out_shapes[0]")
                        code.writeline("_pallas_ax2g = {}")

                # Wrap kernel with functools.partial to pass scalar arguments (size variables)
                partial_args = []
                for sv_param in ctx.size_var_params:
                    partial_args.append(f"{sv_param}={sv_param}")

                if self.tile_relative_iter_vars:
                    partial_args.append("_pallas_tile=_pallas_tile")
                    partial_args.append("_pallas_ax2g=_pallas_ax2g")

                if partial_args:
                    kernel_arg = f"functools.partial({kernel_name}_kernel, {', '.join(partial_args)}),"
                else:
                    kernel_arg = f"{kernel_name}_kernel,"

                use_tma = (
                    self.is_gpu
                    and self.use_emit_pipeline
                    and self._can_use_tma_approach()
                )
                if use_tma:
                    self._codegen_jit_wrapper_tma(ctx, kernel_arg)
                elif self.is_gpu:
                    self._codegen_jit_wrapper_legacy_gpu(ctx, kernel_arg)
                else:
                    self._codegen_jit_wrapper_cpu_tpu(
                        ctx, kernel_arg, ctx.alias_pairs, alias_map_literal
                    )

        self._codegen_main_entry(ctx, jit_wrapper_name)
        return code.getvalue()