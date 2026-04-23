def _codegen_jit_wrapper_tma(self, ctx: _CodegenContext, kernel_arg: str) -> None:
        code = ctx.code
        kernel_input_params = ctx.kernel_input_params
        output_params = ctx.output_params

        # TMA automatically handles out-of-bounds accesses
        code.writeline("# Use lax.fori_loop with TMA for automatic OOB masking")
        code.writeline("from jax import lax")
        code.writeline("_tile_size = 128  # Warpgroup size")
        code.writeline("_orig_out_shapes = out_shapes")

        code.writeline("_max_numel = 0")
        for param in kernel_input_params:
            code.writeline(f"_max_numel = max(_max_numel, {param}.size)")
        code.writeline("for shape in out_shapes:")
        code.writeline("    _max_numel = max(_max_numel, math.prod(shape))")

        code.writeline("_num_tiles = (_max_numel + _tile_size - 1) // _tile_size")

        gmem_input_params = [f"{p}_gmem" for p in kernel_input_params]
        gmem_output_params = [f"{p}_gmem" for p in output_params]
        smem_input_params = [f"{p}_smem" for p in kernel_input_params]
        smem_output_params = [f"{p}_smem" for p in output_params]

        code.writeline("")
        code.writeline("# Wrapper kernel using lax.fori_loop with direct TMA")

        wrapper_kernel_params = gmem_input_params + gmem_output_params
        all_smem_params = smem_input_params + smem_output_params
        barrier_params = [f"_barrier_{i}" for i in range(len(kernel_input_params))]
        scratch_params = ", ".join(all_smem_params + barrier_params)

        code.writeline(
            f"def _tma_kernel({', '.join(wrapper_kernel_params)}, *, {scratch_params}):"
        )
        with code.indent():
            code.writeline("")
            code.writeline("def _tile_body(_tile_idx, _):")
            with code.indent():
                code.writeline("_tile_start = _tile_idx * _tile_size")
                code.writeline("")

                code.writeline("# TMA load inputs from GMEM to SMEM (OOB auto-masked)")
                for i, (gmem_in, smem_in) in enumerate(
                    zip(gmem_input_params, smem_input_params)
                ):
                    code.writeline(
                        f"plgpu.copy_gmem_to_smem({gmem_in}.at[pl.ds(_tile_start, _tile_size)], {smem_in}, _barrier_{i})"
                    )

                code.writeline("")
                code.writeline("# Wait for TMA loads to complete")
                for i, _ in enumerate(gmem_input_params):
                    code.writeline(f"plgpu.barrier_wait(_barrier_{i})")

                code.writeline("")
                code.writeline("# Compute on SMEM tiles")
                kernel_call_args = smem_input_params + smem_output_params
                kernel_fn = kernel_arg.rstrip(",").strip()
                code.writeline(f"{kernel_fn}({', '.join(kernel_call_args)})")

                code.writeline("")
                code.writeline(
                    "# TMA store outputs from SMEM to GMEM (OOB auto-masked)"
                )
                code.writeline("plgpu.commit_smem()")
                for gmem_out, smem_out in zip(gmem_output_params, smem_output_params):
                    code.writeline(
                        f"plgpu.copy_smem_to_gmem({smem_out}, {gmem_out}.at[pl.ds(_tile_start, _tile_size)])"
                    )
                code.writeline("plgpu.wait_smem_to_gmem(0)")
                code.writeline("")
                code.writeline("return None")

            code.writeline("")
            code.writeline("# Iterate over all tiles")
            code.writeline("lax.fori_loop(0, _num_tiles, _tile_body, None)")

        # Build scratch_shapes dict
        code.writeline("")
        code.writeline(
            "# Build SMEM scratch shapes for inputs, outputs, and TMA barriers"
        )
        code.writeline("_scratch_shapes = {}")
        for i, smem_param in enumerate(smem_input_params):
            orig_param = kernel_input_params[i]
            code.writeline(
                f"_scratch_shapes['{smem_param}'] = plgpu.SMEM((_tile_size,), {orig_param}.dtype)"
            )
        for i, smem_param in enumerate(smem_output_params):
            code.writeline(
                f"_scratch_shapes['{smem_param}'] = plgpu.SMEM((_tile_size,), out_dtypes[{i}])"
            )
        for barrier_param in barrier_params:
            code.writeline(
                f"_scratch_shapes['{barrier_param}'] = plgpu.Barrier(num_arrivals=1)"
            )

        code.writeline("")
        code.writeline("# Create flattened output specs aligned to tile size")
        code.writeline(
            "_flat_out_specs, _ = pallas_gpu_align_output_specs(out_shapes, out_dtypes, _tile_size)"
        )

        code.writeline("")
        code.writeline("# Call plgpu.kernel with TMA kernel")
        code.writeline("_result = plgpu.kernel(")
        with code.indent():
            code.writeline("_tma_kernel,")
            code.writeline("out_shape=_flat_out_specs,")
            code.writeline("scratch_shapes=_scratch_shapes,")
        code.writeline(")(")
        for param in kernel_input_params:
            code.writeline(f"    {param}.flatten(),")
        code.writeline(")")

        code.writeline("")
        code.writeline("# Reshape results to original shapes")
        code.writeline("return pallas_gpu_unpad_results(_result, _orig_out_shapes)")