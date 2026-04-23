def test_tma_descriptor_dedup(self, tma_version):
        if tma_version == "new" and not has_triton_tensor_descriptor_host_tma():
            self.skipTest("requires triton.tools.tensor_descriptor TMA support")
        if tma_version == "old" and not has_triton_experimental_host_tma():
            self.skipTest("requires triton.tools.experimental_descriptor TMA support")

        kernel = (
            add_kernel_with_tma_1d_new_api
            if tma_version == "new"
            else add_kernel_with_tma_1d_old_api
        )

        def f(a):
            BLOCK_SIZE = 256
            out = torch.zeros_like(a)
            n_elements = out.numel()

            desc_a, desc_out = (
                create_tensor_descriptor_shim(
                    t, [BLOCK_SIZE], new_api=(tma_version == "new")
                )
                for t in (a, out)
            )

            grid = lambda meta: (triton.cdiv(n_elements, meta["BLOCK_SIZE"]),)
            kernel[grid](
                desc_a,
                desc_a,
                desc_out,
                BLOCK_SIZE=BLOCK_SIZE,
            )

            return out

        a = torch.randn(301, device=GPU_TYPE)

        expected_out = a + a
        eager_out = f(a)
        compiled_out, (code,) = run_and_get_code(
            torch.compile(
                f,
                fullgraph=True,
                backend="inductor",
                dynamic=True,
            ),
            a,
        )

        self.assertEqual(eager_out, expected_out)
        self.assertEqual(compiled_out, expected_out)

        # 2 calls: one for two inputs (dedupped), one for the output
        if tma_version == "new":
            if (
                not inductor_config.cpp_wrapper
                or inductor_config.triton.autotune_at_compile_time
            ):
                # Lazy kernel compilation implicitly calls TensorDescriptor.from_tensor
                # when calling run_triton_kernel_with_autotune
                self.assertEqual(code.count("TensorDescriptor.from_tensor("), 2)
        else:
            self.assertEqual(code.count("create_1d_tma_descriptor("), 2)