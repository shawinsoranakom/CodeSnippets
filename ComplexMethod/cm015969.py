def test_triton_fx_graph_with_et(self, device):
        # clean up the local cache for triton kernel
        from torch._inductor.codecache import PyCodeCache

        PyCodeCache.cache_clear(purge=True)

        @torchdynamo.optimize("inductor")
        def fn(a, b, c):
            x = torch.nn.functional.linear(a, b)
            x = x.sin()
            x = x.t() + c * 1111
            return x.cos()

        a, b, c = (
            torch.randn(4, 4, requires_grad=False).to(torch.device(device))
            for _ in range(3)
        )

        with torch._inductor.config.patch(
            compile_threads=1, fx_graph_cache=False, fx_graph_remote_cache=False
        ):
            fn(a, b, c)

        et = ExecutionTraceObserver()
        with tempfile.NamedTemporaryFile(
            "w+t", suffix="fx_graph_et.json", delete=False
        ) as fp:
            et.register_callback(fp.name)
        et.set_extra_resource_collection(True)
        with profile(
            activities=torch.profiler.supported_activities(),
            record_shapes=True,
            schedule=torch.profiler.schedule(
                skip_first=0, wait=1, warmup=1, active=1, repeat=1
            ),
            execution_trace_observer=et,
        ) as p:
            for idx in range(10):
                with record_function(f"## LOOP {idx} ##"):
                    fn(a, b, c)
                p.step()

        et_path = p.execution_trace_observer.get_output_file_path()
        et_res_path = p.execution_trace_observer.get_resources_dir(et_path)
        # the path should be set up due to our env variables
        self.assertTrue(et_path is not None)
        # et_res_path should be an empty directory
        self.assertTrue(os.path.isdir(et_res_path))
        for filename in os.listdir(et_res_path):
            file_path = os.path.join(et_res_path, filename)
            if os.path.isfile(file_path):
                with open(file_path) as file:
                    fx_graph_found = False
                    fx_graph = []
                    for line in file:
                        line = line.strip()
                        # There are two files in the directory, one is the source
                        # code of the triton kernel, and the other is the source code for FX graph.
                        # Only the FX graph file contains the string "# Graph fragment:".
                        if line.startswith("# Graph fragment:"):
                            fx_graph_found = True
                        elif fx_graph_found and line.startswith("#"):
                            fx_graph.append(line)
                        else:
                            fx_graph_found = False

                    if len(fx_graph) > 0:
                        expected_graph = [
                            f'#   %mm : Tensor "f32[4, 4][4, 1]{device}" = PlaceHolder[target=mm]',
                            f'#   %arg2_1 : Tensor "f32[4, 4][4, 1]{device}" = PlaceHolder[target=arg2_1]',
                            f'#   %sin : Tensor "f32[4, 4][4, 1]{device}"[num_users=1] = call_function[target=torch.ops.aten.sin.default](args = (%mm,), kwargs = {{}})',
                            f'#   %permute_1 : Tensor "f32[4, 4][1, 4]{device}"[num_users=1] = call_function[target=torch.ops.aten.permute.default](args = (%sin, [1, 0]), kwargs = {{}})',
                            f'#   %mul : Tensor "f32[4, 4][4, 1]{device}"[num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%arg2_1, 1111), kwargs = {{}})',
                            f'#   %add : Tensor "f32[4, 4][1, 4]{device}"[num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%permute_1, %mul), kwargs = {{}})',
                            f'#   %cos : Tensor "f32[4, 4][1, 4]{device}"[num_users=1] = call_function[target=torch.ops.aten.cos.default](args = (%add,), kwargs = {{}})',
                            "#   return %cos",
                        ]
                        if len(fx_graph) < len(expected_graph):
                            raise AssertionError(
                                f"Expected at least {len(expected_graph)} fx_graph lines, "
                                f"got {len(fx_graph)}"
                            )
                        for idx, expected in enumerate(expected_graph):
                            if fx_graph[idx] != expected:
                                raise AssertionError(
                                    f"Expected fx_graph[{idx}] to be {expected}, got {fx_graph[idx]}"
                                )
                os.remove(file_path)