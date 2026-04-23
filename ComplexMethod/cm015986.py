def test_memory_profiler(self):
        def run_profiler(tensor_creation_fn):
            # collecting allocs / deallocs
            with _profile(
                profile_memory=True,
                record_shapes=True,
                use_kineto=kineto_available(),
            ) as prof:
                x = None
                with record_function("test_user_scope_alloc"):
                    x = tensor_creation_fn()
                with record_function("test_user_scope_dealloc"):
                    del x
            return prof.key_averages(group_by_input_shape=True)

        def check_metrics(stats, metric, allocs=None, deallocs=None):
            stat_metrics = {}
            # print(stats)
            for stat in stats:
                stat_metrics[stat.key] = getattr(stat, metric)
            # print(stat_metrics)
            if allocs is not None:
                for alloc_fn in allocs:
                    self.assertTrue(alloc_fn in stat_metrics)
                    self.assertGreater(
                        stat_metrics[alloc_fn], 0, f"alloc_fn = {alloc_fn}"
                    )
            if deallocs is not None:
                for dealloc_fn in deallocs:
                    self.assertTrue(dealloc_fn in stat_metrics)
                    self.assertLess(
                        stat_metrics[dealloc_fn], 0, f"alloc_fn = {dealloc_fn}"
                    )

        def create_cpu_tensor():
            return torch.rand(10, 10)

        def create_cuda_tensor():
            return torch.rand(10, 10).cuda()

        def create_xpu_tensor():
            return torch.rand(10, 10).xpu()

        def create_mkldnn_tensor():
            return torch.rand(10, 10, dtype=torch.float32).to_mkldnn()

        stats = run_profiler(create_cpu_tensor)
        check_metrics(
            stats,
            "cpu_memory_usage",
            allocs=[
                "aten::empty",
                "aten::rand",
                "test_user_scope_alloc",
            ],
            deallocs=[
                "test_user_scope_dealloc",
            ],
        )

        if kineto_available():
            with TemporaryFileName(mode="w+") as fname:
                with profile(profile_memory=True) as prof:
                    x = None
                    with record_function("test_user_scope_alloc"):
                        x = create_cpu_tensor()
                    with record_function("test_user_scope_dealloc"):
                        del x
                prof.export_chrome_trace(fname)
                with open(fname) as f:
                    trace = json.load(f)
                    if "traceEvents" not in trace:
                        raise AssertionError("Expected 'traceEvents' in trace")
                    events = trace["traceEvents"]
                    found_memory_events = False
                    for evt in events:
                        if "name" not in evt:
                            raise AssertionError("Expected 'name' in event")
                        if evt["name"] == "[memory]":
                            found_memory_events = True
                            if "args" not in evt:
                                raise AssertionError("Expected 'args' in memory event")
                            if "Addr" not in evt["args"]:
                                raise AssertionError("Expected 'Addr' in event args")
                            if "Device Type" not in evt["args"]:
                                raise AssertionError(
                                    "Expected 'Device Type' in event args"
                                )
                            if "Device Id" not in evt["args"]:
                                raise AssertionError(
                                    "Expected 'Device Id' in event args"
                                )
                            if "Bytes" not in evt["args"]:
                                raise AssertionError("Expected 'Bytes' in event args")

                            # Memory should be an instantaneous event.
                            if "dur" in evt["args"]:
                                raise AssertionError("Unexpected 'dur' in event args")
                            if "cat" in evt["args"]:
                                raise AssertionError("Unexpected 'cat' in event args")
                    if not found_memory_events:
                        raise AssertionError("Expected to find memory events")

        if torch.cuda.is_available():
            create_cuda_tensor()
            stats = run_profiler(create_cuda_tensor)
            check_metrics(
                stats,
                "device_memory_usage",
                allocs=[
                    "test_user_scope_alloc",
                    "aten::to",
                    "aten::empty_strided",
                ],
                deallocs=[
                    "test_user_scope_dealloc",
                ],
            )
            check_metrics(
                stats,
                "cpu_memory_usage",
                allocs=[
                    "aten::rand",
                    "aten::empty",
                ],
            )

        if torch.xpu.is_available():
            create_xpu_tensor()
            stats = run_profiler(create_xpu_tensor)
            check_metrics(
                stats,
                "device_memory_usage",
                allocs=[
                    "test_user_scope_alloc",
                    "aten::to",
                    "aten::empty_strided",
                ],
                deallocs=[
                    "test_user_scope_dealloc",
                ],
            )
            check_metrics(
                stats,
                "cpu_memory_usage",
                allocs=[
                    "aten::rand",
                    "aten::empty",
                ],
            )

        if torch.backends.mkldnn.is_available():
            create_mkldnn_tensor()
            stats = run_profiler(create_mkldnn_tensor)
            check_metrics(
                stats,
                "cpu_memory_usage",
                allocs=[
                    "test_user_scope_alloc",
                    "aten::rand",
                    "aten::empty",
                    "aten::to_mkldnn",
                ],
                deallocs=[
                    "test_user_scope_dealloc",
                ],
            )

        # check top-level memory events
        with _profile(profile_memory=True, use_kineto=kineto_available()) as prof:
            x = torch.rand(10, 10)
            del x
            if torch.cuda.is_available():
                y = torch.rand(10, 10).cuda()
                del y
            elif torch.xpu.is_available():
                y = torch.rand(10, 10).to("xpu")
                del y
            gc.collect()
        stats = prof.key_averages(group_by_input_shape=True)
        check_metrics(
            stats,
            "cpu_memory_usage",
            allocs=["aten::rand", "aten::empty"],
            deallocs=["[memory]"],
        )
        if torch.cuda.is_available():
            check_metrics(stats, "device_memory_usage", deallocs=["[memory]"])
        elif torch.xpu.is_available():
            check_metrics(stats, "device_memory_usage", deallocs=["[memory]"])