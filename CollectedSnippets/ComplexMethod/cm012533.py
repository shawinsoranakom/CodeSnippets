def _codegen_main_entry_default(
        self, ctx: _CodegenContext, jit_wrapper_name: str
    ) -> None:
        code = ctx.code
        code.writeline("")
        main_name = f"{ctx.kernel_name}_main"
        code.writeline(
            f"def {main_name}({', '.join(ctx.full_kernel_params)}, stream=None):"
        )
        with code.indent():
            code.writeline("jax.config.update('jax_enable_x64', True)")
            if ctx.interpret_is_cpu:
                code.writeline(
                    "jax.config.update('jax_default_device', jax.devices('cpu')[0])"
                )
            code.writeline("jax.clear_caches()")
            if ctx.alias_params:
                code.writeline("# Convert Torch -> JAX for donated outputs")
                for alias_name in ctx.alias_params:
                    # On CPU/TPU, alias outputs may be non-contiguous (e.g.
                    # torch.cat slices) and JAX's from_dlpack rejects
                    # non-trivially strided tensors.  Making them contiguous
                    # is safe because CPU/TPU already copies all results back
                    # via copy_output_indices.  On CUDA, the donated-buffer
                    # mechanism requires the original buffer for in-place
                    # mutation, so we cannot make a contiguous copy.
                    self._emit_torch_to_jax(
                        code,
                        alias_name,
                        ctx.is_tpu,
                        contiguous=ctx.interpret_is_cpu,
                    )
            code.writeline("# Convert Torch -> JAX for in-place tensors")
            for ptr in ctx.pointer_tail:
                if ptr.startswith("in_out_ptr"):
                    self._emit_torch_to_jax(code, ptr, ctx.is_tpu, contiguous=False)
            code.writeline("# Convert Torch -> JAX for inputs")
            for ptr in ctx.pointer_tail:
                if ptr.startswith("in_ptr"):
                    self._emit_torch_to_jax(code, ptr, ctx.is_tpu, contiguous=True)

            code.writeline("# Prepare output metadata from PyTorch tensor")
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
            arg_name_map: dict[str, str] = {}
            for alias_name in ctx.alias_params:
                arg_name_map[alias_name] = f"{alias_name}_jax"
            for ptr in ctx.pointer_tail:
                arg_name_map[ptr] = f"{ptr}_jax"

            wrapper_call_args = ["out_shapes", "out_dtypes"]
            wrapper_call_args.extend(ctx.size_var_params)
            wrapper_call_args.extend(
                arg_name_map[name] for name in ctx.kernel_input_params
            )
            code.writeline(f"res = {jit_wrapper_name}({', '.join(wrapper_call_args)})")
            code.writeline("jax.block_until_ready(res)")
            if ctx.copy_output_indices:
                code.writeline(
                    "result_values = res if isinstance(res, tuple) else (res,)"
                )
                for idx in ctx.copy_output_indices:
                    out_name = ctx.output_params[idx]
                    code.writeline(
                        f"{out_name}.copy_(torch.from_dlpack(result_values[{idx}]))"
                    )