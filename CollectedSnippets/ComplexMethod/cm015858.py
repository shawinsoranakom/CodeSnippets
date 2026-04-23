def test_simple(self, embed_kernel_binary, max_autotune):
        if self.device == "cpu" and IS_MACOS and max_autotune:
            raise unittest.SkipTest("max_autotune not supported on macos")

        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear = torch.nn.Linear(10, 10)

            def forward(self, x, y):
                return x + self.linear(y)

        example_inputs = (
            torch.randn(10, 10, device=self.device),
            torch.randn(10, 10, device=self.device),
        )
        model = Model()
        with config.patch(
            {
                "aot_inductor.embed_kernel_binary": embed_kernel_binary,
                "max_autotune": max_autotune,
            }
        ):
            self.check_model(model, example_inputs)

            _, code = run_and_get_cpp_code(
                AOTIRunnerUtil.compile, model, example_inputs
            )
            if self.device == "mps":
                FileCheck().check("aoti_torch_mps_get_kernel_function(").run(code)
            elif self.device == GPU_TYPE:
                FileCheck().check("launchKernel(").run(code)
                if config.aot_inductor.embed_kernel_binary:
                    # Not expect to see launchKernel("CUBIN_FILE_NAME"
                    FileCheck().check_not('launchKernel("').run(code)

        if self.use_minimal_arrayref_interface:
            self.code_check_count(
                model, example_inputs, "AOTInductorModelRunMinimalArrayrefInterface(", 1
            )