def test_triton_kernel_on_device_tma(self, dynamic, tma_version):
        if self.device != GPU_TYPE:
            raise unittest.SkipTest("requires GPU")
        if tma_version == "new" and not has_triton_tensor_descriptor_host_tma():
            self.skipTest("requires triton.tools.tensor_descriptor TMA support")
        if tma_version == "old" and not has_triton_experimental_host_tma():
            self.skipTest("requires triton.tools.experimental_descriptor TMA support")

        kernel = (
            add_kernel_on_device_tma_new_api
            if tma_version == "new"
            else add_kernel_on_device_tma_old_api
        )

        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()

            def forward(self, a, b):
                BLOCK_SIZE = 32
                out = torch.zeros_like(a)
                m, n = out.size()

                # Allocate workspace for on-device TMA descriptors
                # Need 128 bytes per descriptor, 3 descriptors total
                if tma_version == "old":
                    workspace = torch.zeros(3 * 128, dtype=torch.uint8, device=a.device)
                else:
                    workspace = None

                grid = (triton.cdiv(m, BLOCK_SIZE), triton.cdiv(n, BLOCK_SIZE))

                kernel[grid](
                    a,
                    b,
                    out,
                    m,
                    n,
                    workspace,
                    BLOCK_SIZE=BLOCK_SIZE,
                )

                return out

        a = torch.randn((32 * 4, 32 * 8), device=self.device)
        b = torch.randn((32 * 4, 32 * 8), device=self.device)
        example_inputs = (a, b)

        triton.set_allocator(
            lambda size, align, stream: torch.empty(
                size, dtype=torch.int8, device=GPU_TYPE
            )
        )

        dynamic_shapes = None
        if dynamic:
            dim0 = Dim("s0", min=2, max=1024)
            dim1 = Dim("s1", min=2, max=1024)
            dynamic_shapes = {
                "a": {0: dim0, 1: None},
                "b": {0: dim1, 1: None},
            }

        self.check_model(
            Model(),
            example_inputs=example_inputs,
            dynamic_shapes=dynamic_shapes,
        )