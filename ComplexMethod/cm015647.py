def test_graph_break_partial_backend(self, device):
        if device == "cuda" and not HAS_CUDA_AND_TRITON:
            raise unittest.SkipTest("Requires CUDA/Triton")
        if device == "xpu" and not HAS_XPU_AND_TRITON:
            raise unittest.SkipTest("Requires XPU/Triton")

        def fn(x):
            y = x.sin()
            torch._dynamo.graph_break()
            return x.sin() + y

        arg1 = torch.randn(3, 2, device=device, requires_grad=True)
        arg2 = arg1.clone().detach_().requires_grad_(True)
        compiled_fn = torch.compile(fn)
        expected1 = compiled_fn(arg1)
        expected1.sum().backward()
        total_frames = torch._dynamo.convert_frame.FRAME_COUNTER

        # Remove backends related to resume functions
        dynamo_entry = next(iter(PrecompileContext._dynamo_cache_entries.values()))
        for code in dynamo_entry.codes:
            module = sys.modules[code.python_module]
            if code.install_to_global:
                # Clear the fn_names from global scope, to simulate a new environment
                for fn_name in code.function_names:
                    module.__dict__.pop(fn_name)
            for fn_name in code.function_names:
                if "resume" in fn_name:
                    self.assertEqual(len(code.backend_ids), 1)
                    # delete the fn from the global scope to simulate a new
                    backend = code.backend_ids[0]
                    # Delete the backend associated with the resume function
                    del PrecompileContext._backend_artifacts_by_key[backend]

        self._save_and_reload(expected_backends=1, expected_dynamo=1)

        compiled_fn = torch.compile(fn)
        # Run it again. There will be a recompile because one of the backends is deleted, but it should
        # still work.
        expected2 = compiled_fn(arg2)
        expected2.sum().backward()
        self.assertEqual(expected1, expected2)
        # One recompile on a new frame, so total_frames should increase by 1
        self.assertEqual(torch._dynamo.convert_frame.FRAME_COUNTER, total_frames + 1)