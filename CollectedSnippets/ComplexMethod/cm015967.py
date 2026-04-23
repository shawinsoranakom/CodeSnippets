def test_execution_trace_with_pt2(self, device):
        @torchdynamo.optimize("inductor")
        def fn(a, b, c):
            x = torch.nn.functional.linear(a, b)
            x = x + c
            return x.cos()

        a, b, c = (torch.randn(4, 4, requires_grad=True).to(device) for _ in range(3))

        inputs = [a, b, c]
        with torch._inductor.config.patch(compile_threads=1):
            fn(*inputs)

        # Create a temp file to save execution trace data.
        with tempfile.NamedTemporaryFile("w+t", suffix="_et.json", delete=False) as fp:
            filename = fp.name
        et = ExecutionTraceObserver()
        et.register_callback(filename)
        et.set_extra_resource_collection(True)

        with profile(
            activities=torch.profiler.supported_activities(),
            record_shapes=True,
            schedule=torch.profiler.schedule(
                skip_first=3, wait=1, warmup=1, active=2, repeat=1
            ),
            execution_trace_observer=et,
        ) as p:
            for idx in range(10):
                with record_function(f"## LOOP {idx} ##"):
                    fn(*inputs)
                p.step()

        nodes = self.get_execution_trace_root(filename)
        os.remove(filename)
        found_captured_triton_kernel_node = False
        found_call_compiled_fx_graph = False
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
            elif "Call CompiledFxGraph" in n["name"]:
                found_call_compiled_fx_graph = True
        if not found_captured_triton_kernel_node:
            raise AssertionError("Expected captured triton kernel node")
        if not found_call_compiled_fx_graph:
            raise AssertionError("Expected Call CompiledFxGraph node")