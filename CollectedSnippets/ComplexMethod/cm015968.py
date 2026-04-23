def test_execution_trace_env_enabled_with_pt2(self, device):
        # clean up the local cache for triton kernel
        from torch._inductor.codecache import PyCodeCache

        PyCodeCache.cache_clear(purge=True)

        @torchdynamo.optimize("inductor")
        def fn(a, b, c):
            x = torch.nn.functional.linear(a, b)
            x = x + c
            return x.cos()

        a, b, c = (torch.randn(4, 4, requires_grad=True).to(device) for _ in range(3))

        inputs = [a, b, c]
        with torch._inductor.config.patch(
            compile_threads=1, fx_graph_cache=False, fx_graph_remote_cache=False
        ):
            fn(*inputs)

        with profile(
            activities=torch.profiler.supported_activities(),
            record_shapes=True,
            schedule=torch.profiler.schedule(
                skip_first=3, wait=1, warmup=1, active=2, repeat=1
            ),
        ) as p:
            for idx in range(10):
                with record_function(f"## LOOP {idx} ##"):
                    fn(*inputs)
                p.step()

        et_path = p.execution_trace_observer.get_output_file_path()
        et_res_path = p.execution_trace_observer.get_resources_dir(et_path)
        # the path should be set up due to our env variables
        self.assertTrue(et_path is not None)
        # et_res_path should be an empty directory
        self.assertTrue(os.path.isdir(et_res_path))
        self.assertEqual(len(os.listdir(et_res_path)), 2)
        nodes = self.get_execution_trace_root(et_path)
        found_captured_triton_kernel_node = False
        for n in nodes:
            if "name" not in n:
                raise AssertionError(f"Expected node to have 'name': {n}")
            if "triton_" in n["name"]:
                for attr in n["attrs"]:
                    if attr["name"] == "kernel_file" and attr["value"] != "":
                        found_captured_triton_kernel_node = True
                        if len(n["inputs"]["values"]) <= 0:
                            raise AssertionError(
                                "Expected triton node to have input values"
                            )
                        if len(n["outputs"]["values"]) != 0:
                            raise AssertionError(
                                "Expected triton node to have no output values"
                            )
        if not found_captured_triton_kernel_node:
            raise AssertionError("Expected captured triton kernel node")