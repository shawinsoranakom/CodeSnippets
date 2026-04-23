def test_triton_kernel_no_clones(self, grad, dynamic):
        from torch._inductor.utils import run_and_get_code

        def call_triton(x: torch.Tensor, y: torch.Tensor, output: torch.Tensor):
            n_elements = output.numel()

            tmp = torch.add(x, 1)
            grid = (x.numel(),)
            add_kernel.run(
                x, y, output, n_elements, warmup=False, grid=grid, BLOCK_SIZE=16
            )

            return output, tmp

        t1 = torch.rand(5, device=GPU_TYPE, requires_grad=grad)
        t2 = torch.rand(5, device=GPU_TYPE, requires_grad=grad)
        o1 = torch.zeros_like(t1, requires_grad=grad)

        torch_add = call_triton(t1, t2, o1)
        metrics.reset()
        o2 = torch.zeros_like(t1, requires_grad=grad)
        test, (code,) = run_and_get_code(
            torch.compile(call_triton, dynamic=dynamic), t1, t2, o2
        )
        if not grad:
            self.assertEqual(metrics.generated_kernel_count, 1)
        self.assertEqual(torch_add, test)
        # These two asserts are not optimal since it requires original aten
        # to be in the metadata, so there might be false negatives
        self.assertNotIn(
            "aoti_torch_copy_" if inductor_config.cpp_wrapper else "aten.copy", code
        )
        self.assertNotIn(
            "aoti_torch_clone" if inductor_config.cpp_wrapper else "aten.clone", code
        )
        # The following checks that there are only the tensor output is in
        # the compiled graph
        if dynamic and grad:
            if inductor_config.cpp_wrapper:
                self.assertIn("output_handles[0] = ", code)
                self.assertIn("output_handles[1] = ", code)
            else:
                self.assertIn("return (buf0, s92, )", code)
        else:
            self.assertIn(
                "output_handles[0] = "
                if inductor_config.cpp_wrapper
                else "return (buf0, )",
                code,
            )