def test_aoti_debug_printer_codegen(self):
        # basic addmm model to test codegen for aoti intermediate debug printer
        class Model(torch.nn.Module):
            def __init__(self, n, k, device):
                super().__init__()
                self.weight = torch.randn(n, k, device=device)
                self.bias = torch.randn(n, device=device)

            def forward(self, a):
                return torch.nn.functional.linear(a, self.weight, self.bias)

        M = 8
        N = 6
        K = 16
        model = Model(N, K, self.device)
        batch = 2
        a = torch.randn(batch, M, K, device=self.device)
        example_inputs = (a,)

        if self.device == "mps":
            kernel_calls = [("aoti_torch_mps_addmm_out", 2)]
        elif self.device == GPU_TYPE:
            kernel_calls = [
                ("triton_poi_fused_0", 1),
                (f"aoti_torch_{GPU_TYPE}_addmm_out", 2),
            ]
        else:
            kernel_calls = [("aoti_torch_cpu_addmm_out", 2)]

        # test default debug printing all tensor values codegen
        with config.patch({"aot_inductor.debug_intermediate_value_printer": "2"}):
            result, code = run_and_get_cpp_code(
                AOTIRunnerUtil.legacy_compile, model, example_inputs
            )

            # check the c shim print_tensor_handle call is triggered by the config and injected the cpp output code as expected
            self.assertEqual("aoti_torch_print_tensor_handle" in code, True)

            # check the codegen for debug printing around the actual kernel call is expected

            for kernel_call, count in kernel_calls:
                FileCheck().check_count(
                    f"before_launch - {kernel_call}",
                    count,
                ).run(code)
                FileCheck().check_count(
                    f"after_launch - {kernel_call}",
                    count,
                ).run(code)

        # test printing selected kernel's tensor values codegen
        filtered_kernel_name = f"aoti_torch_{self.device}_addmm_out"
        with config.patch(
            {
                "aot_inductor.debug_intermediate_value_printer": "2",
                "aot_inductor.filtered_kernel_names": filtered_kernel_name,
            }
        ):
            result, code = run_and_get_cpp_code(
                AOTIRunnerUtil.legacy_compile, model, example_inputs
            )
            filtered_kernel_calls = [
                (filtered_kernel_name, 2),
            ]
            for kernel_call, count in filtered_kernel_calls:
                FileCheck().check_count(
                    f"before_launch - {kernel_call}",
                    count,
                ).run(code)
                FileCheck().check_count(
                    f"after_launch - {kernel_call}",
                    count,
                ).run(code)

            kernel_calls_not_to_print = [
                kernel_call
                for kernel_call in kernel_calls
                if kernel_call[0] != filtered_kernel_name
            ]
            for kernel_name, _ in kernel_calls_not_to_print:
                FileCheck().check_not(f"before_launch - {kernel_name}").run(code)
                FileCheck().check_not(f"after_launch - {kernel_name}").run(code)