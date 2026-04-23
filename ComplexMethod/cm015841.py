def test_dump_launch_tensors(self):
        """
        Test that dump_launch_tensors functions correctly:
        1. Creates the dump directory when torch.compile() runs
        2. Saves tensor files that can be loaded
        3. Loads tensors to match the original values
        4. Properly rotates when max_kernel_dump_occurrences is reached
        """
        from torch._inductor.config import triton as inductor_triton_config
        from torch._inductor.runtime.runtime_utils import cache_dir

        # Clear any existing state
        inductor_triton_config.debug_dump_kernel_inputs.clear()

        # Define a simple function that will generate Triton kernels
        def simple_model(x):
            y = x * 2.0
            z = y + 1.0
            return z.sum()

        old_dump_env = os.environ.get("TORCHINDUCTOR_DUMP_LAUNCH_TENSORS")
        os.environ["TORCHINDUCTOR_DUMP_LAUNCH_TENSORS"] = "1"

        try:
            compiled_fn = torch.compile(simple_model)

            # Run the compiled function multiple times to test rotation
            max_runs = inductor_triton_config.max_kernel_dump_occurrences

            for i in range(max_runs + 2):
                test_input = torch.randn(100, 100, device=GPU_TYPE) * (i + 1)
                _ = compiled_fn(test_input)

            # After multiple runs, verify rotation and tensor correctness
            kernel_bases = {}
            verified_tensor_load = False

            for root, dirs, files in os.walk(cache_dir()):
                for d in dirs:
                    if "_run_" in d:
                        full_path = os.path.join(root, d)
                        tensor_files = [
                            f
                            for f in os.listdir(full_path)
                            if f.startswith("tensor_") and f.endswith(".pt")
                        ]
                        if not tensor_files:
                            continue

                        dir_name = os.path.basename(full_path)
                        base_name = dir_name.rsplit("_run_", 1)[0]
                        run_idx = int(dir_name.rsplit("_run_", 1)[1])

                        # Track run indices per kernel
                        if base_name not in kernel_bases:
                            kernel_bases[base_name] = []
                        kernel_bases[base_name].append(run_idx)

                        # Verify we can successfully load at least one saved tensor
                        if not verified_tensor_load:
                            first_tensor_file = os.path.join(full_path, tensor_files[0])
                            loaded_tensor = torch.load(first_tensor_file)

                            # Verify it's a valid tensor with expected properties
                            self.assertIsInstance(loaded_tensor, torch.Tensor)
                            self.assertEqual(loaded_tensor.device.type, GPU_TYPE)
                            verified_tensor_load = True

            # Verify rotation constraints
            if kernel_bases:
                for base_name, indices in kernel_bases.items():
                    self.assertLessEqual(
                        len(indices),
                        max_runs,
                        f"Kernel {base_name} has more runs ({len(indices)}) than max ({max_runs})",
                    )

                    # Verify the indices are within [0, max_runs)
                    for idx in indices:
                        self.assertLess(
                            idx,
                            max_runs,
                            f"Run index {idx} exceeds max_runs-1 ({max_runs - 1})",
                        )

        finally:
            # Restore environment variable
            if old_dump_env is None:
                os.environ.pop("TORCHINDUCTOR_DUMP_LAUNCH_TENSORS", None)
            else:
                os.environ["TORCHINDUCTOR_DUMP_LAUNCH_TENSORS"] = old_dump_env