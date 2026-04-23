def test(
            fn, inps, has_assert: bool, has_wrapping: bool, vectorize: bool = True
        ):
            fn_opt = torch.compile(fn)
            if is_halide_backend(self.device):
                pass  # no device asserts in halide
            elif is_mps_backend(self.device):
                _, codes = run_and_get_code(fn_opt, *inps)
                # MPS generates Metal shader code
                code = "\n".join(codes)
                # Check for error reporting in MPS kernels
                self.assertTrue(("TORCH_REPORT_ERROR" in code) is has_assert)
                # Check for wrapping (ternary operator for negative index handling)
                self.assertTrue((" ? " in code) is has_wrapping)
            elif is_pallas_backend(self.device):
                pass  # Pallas generates Python/JAX code, not C++/Triton
            elif self.device == "cpu" and not is_triton_cpu_backend(self.device):
                _, code = run_and_get_cpp_code(fn_opt, *inps)
                self.assertTrue(("TORCH_CHECK" in code) is has_assert)
                if (
                    cpu_vec_isa.valid_vec_isa_list()
                    and os.getenv("ATEN_CPU_CAPABILITY") != "default"
                ):
                    self.assertTrue(
                        (") ? (" in code or "blendv" in code) is has_wrapping
                    )
                    # Assert that we always vectorize the kernel regardless of wrapping / checks
                    self.assertTrue(("loadu" in code) is vectorize)
            else:
                code = run_and_get_triton_code(fn_opt, *inps)
                self.assertTrue(("tl.where" in code) is has_wrapping)
                self.assertTrue(("device_assert" in code) is has_assert)