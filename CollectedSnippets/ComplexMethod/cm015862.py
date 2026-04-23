def test_triton_kernel_tma_descriptor_2d(self, dynamic, tma_version):
        if self.device != GPU_TYPE:
            raise unittest.SkipTest("requires GPU")
        if tma_version == "new" and not has_triton_tensor_descriptor_host_tma():
            self.skipTest("requires triton.tools.tensor_descriptor TMA support")
        if tma_version == "old" and not has_triton_experimental_host_tma():
            self.skipTest("requires triton.tools.experimental_descriptor TMA support")

        kernel = (
            add_kernel_with_tma_2d_new_api
            if tma_version == "new"
            else add_kernel_with_tma_2d_old_api
        )

        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()

            def forward(self, a, b):
                BLOCK_SIZE_X = 16
                BLOCK_SIZE_Y = 32
                out = torch.zeros_like(a)
                x_size, y_size = out.size()

                desc_a, desc_b, desc_out = (
                    create_tensor_descriptor_shim(
                        t,
                        [BLOCK_SIZE_X, BLOCK_SIZE_Y],
                        new_api=(tma_version == "new"),
                    )
                    for t in (a, b, out)
                )

                grid = lambda meta: (  # noqa: E731
                    triton.cdiv(x_size, meta["BLOCK_SIZE_X"]),
                    triton.cdiv(y_size, meta["BLOCK_SIZE_Y"]),
                )
                kernel[grid](
                    desc_a,
                    desc_b,
                    desc_out,
                    BLOCK_SIZE_X=BLOCK_SIZE_X,
                    BLOCK_SIZE_Y=BLOCK_SIZE_Y,
                )

                return out

        a = torch.randn((25, 16), device=self.device)
        b = torch.randn((25, 16), device=self.device)
        example_inputs = (a, b)

        dynamic_shapes = None
        if dynamic:
            dim0_ab = Dim("s0", min=2, max=1024)
            dynamic_shapes = {
                "a": {0: dim0_ab, 1: None},
                "b": {0: dim0_ab, 1: None},
            }

        self.check_model(
            Model(),
            example_inputs=example_inputs,
            dynamic_shapes=dynamic_shapes,
        )