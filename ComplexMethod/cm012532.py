def _codegen_main_entry_tpu(
        self, ctx: _CodegenContext, jit_wrapper_name: str
    ) -> None:
        code = ctx.code
        code.writeline("")
        main_name = f"{ctx.kernel_name}_main"
        kernel_name_str = ctx.kernel_name
        code.writeline(
            f"def {main_name}({', '.join(ctx.full_kernel_params)}, stream=None):"
        )
        with code.indent():
            # `jax_enable_x64` is per-process. The CPU path sets it to True,
            # so running both CPU and TPU tests in one process can cause
            # x64-related TPU crashes if we do not explicitly set it to
            # False here.
            code.writeline("jax.config.update('jax_enable_x64', False)")
            code.writeline("jax.clear_caches()")

            # Convert int64 inputs to int32 (TPU doesn't support int64)
            all_input_params = list(ctx.alias_params) + list(ctx.pointer_tail)
            for param_name in all_input_params:
                code.writeline(
                    f"{param_name} = {param_name}.to(torch.int32) "
                    f"if {param_name}.dtype == torch.int64 else {param_name}"
                )

            # Build JAX placeholders for all inputs
            code.writeline("# Build JAX placeholders for export tracing")
            all_jax_input_names = []
            for alias_name in ctx.alias_params:
                code.writeline(
                    f"{alias_name}_placeholder = jax.ShapeDtypeStruct("
                    f"{alias_name}.shape, torch_dtype_to_jax_runtime({alias_name}.dtype))"
                )
                all_jax_input_names.append(f"{alias_name}_placeholder")
            for ptr in ctx.pointer_tail:
                code.writeline(
                    f"{ptr}_placeholder = jax.ShapeDtypeStruct("
                    f"{ptr}.shape, torch_dtype_to_jax_runtime({ptr}.dtype))"
                )
                all_jax_input_names.append(f"{ptr}_placeholder")

            # Prepare output metadata
            code.writeline(
                "out_shapes = ("
                + ", ".join([f"tuple({name}.shape)" for name in ctx.output_params])
                + ",)"
            )
            dtype_exprs: list[str] = []
            for name in ctx.output_params:
                buf_name = ctx.output_buffer_lookup.get(name)
                if buf_name is not None:
                    dtype = V.graph.get_dtype(buf_name)
                    if dtype is not None:
                        dtype_exprs.append(torch_dtype_to_jax(dtype))
                        continue
                dtype_exprs.append(f"torch_dtype_to_jax_runtime({name}.dtype)")
            code.writeline("out_dtypes = (" + ", ".join(dtype_exprs) + ",)")

            # Export the jit_wrapper
            wrapper_placeholder_args = ["out_shapes", "out_dtypes"]
            wrapper_placeholder_args.extend(ctx.size_var_params)
            wrapper_placeholder_args.extend(all_jax_input_names)
            code.writeline(
                f"exported = jax.export.export("
                f"{jit_wrapper_name}, platforms=['tpu'])"
                f"({', '.join(wrapper_placeholder_args)})"
            )

            # Register and call via tpu_torch_pallas
            # Include all output and input shapes in the key to avoid stale
            # cache hits when the same kernel name is compiled with different
            # input/output ranks (e.g. broadcasting vs non-broadcasting calls).
            shape_key_parts = []
            for p in ctx.output_params:
                shape_key_parts.append(f"'_'.join(str(s) for s in {p}.shape)")
            output_key_expr = (
                " + 'x' + ".join(shape_key_parts) if shape_key_parts else "''"
            )
            input_key_parts = []
            for p in ctx.kernel_input_params:
                input_key_parts.append(f"'_'.join(str(s) for s in {p}.shape)")
            input_key_expr = (
                " + 'x' + ".join(input_key_parts) if input_key_parts else "''"
            )
            code.writeline(
                f"kernel_key = '{kernel_name_str}_out_' + "
                f"{output_key_expr}"
                f" + '_in_' + {input_key_expr}"
            )

            code.writeline(
                f"if not tpu_torch_pallas.lookup_custom_kernel('{kernel_name_str}', kernel_key):"
            )
            with code.indent():
                code.writeline("try:")
                with code.indent():
                    code.writeline(
                        f"tpu_torch_pallas.register_custom_kernel("
                        f"'{kernel_name_str}', kernel_key, "
                        f"serialized_mlir_module=exported.mlir_module_serialized)"
                    )
                code.writeline("except TypeError:")
                with code.indent():
                    code.writeline(
                        f"tpu_torch_pallas.register_custom_kernel("
                        f"'{kernel_name_str}', kernel_key, "
                        f"exported.mlir_module_serialized)"
                    )

            # Build input tensor list (all non-size-var inputs)
            input_tensor_names = list(ctx.alias_params) + list(ctx.pointer_tail)
            code.writeline(f"input_tensors = [{', '.join(input_tensor_names)}]")

            # Build output shapes list
            code.writeline("output_shape_tensors = [")
            with code.indent():
                for name in ctx.output_params:
                    buf_name = ctx.output_buffer_lookup.get(name)
                    if buf_name is not None:
                        dtype = V.graph.get_dtype(buf_name)
                        if dtype is not None:
                            code.writeline(
                                f"torch.empty({name}.shape, dtype={dtype!r}, device='tpu'),"
                            )
                            continue
                    code.writeline(
                        f"torch.empty({name}.shape, dtype={name}.dtype, device='tpu'),"
                    )
            code.writeline("]")

            # Build input_output_aliases for zero-copy donation
            if ctx.alias_pairs:
                alias_map_str = ", ".join(f"{i}: {o}" for (i, o) in ctx.alias_pairs)
                code.writeline(f"_input_output_aliases = {{ {alias_map_str} }}")
            else:
                code.writeline("_input_output_aliases = {}")

            code.writeline("try:")
            with code.indent():
                code.writeline(
                    f"tpu_torch_pallas.call_custom_kernel("
                    f"'{kernel_name_str}', kernel_key, "
                    f"inputs=input_tensors, "
                    f"output_shapes=output_shape_tensors, "
                    f"input_output_aliases=_input_output_aliases)"
                )
            code.writeline("except TypeError:")
            with code.indent():
                code.writeline(
                    f"tpu_torch_pallas.call_custom_kernel("
                    f"input_tensors, output_shape_tensors, "
                    f"'{kernel_name_str}', kernel_key, "
                    f"_input_output_aliases)"
                )