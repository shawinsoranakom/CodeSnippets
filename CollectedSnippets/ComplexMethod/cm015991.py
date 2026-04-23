def test_profiler_op_event_kwargs(self):
        x, y = (torch.rand((4, 4)) for _ in range(2))
        with profile(record_shapes=True) as p:
            cm = torch._C._profiler._RecordFunctionFast(
                "add_test_kwinputs",
                [x, y],
                {
                    "stream": 0,
                    "grid": "lambda x : x + 1",
                    "debug": 'debug"',
                    "boolean": True,
                },
            )
            for _ in range(4):
                with cm:
                    x.add(y)
        with TemporaryFileName(mode="w+") as fname:
            p.export_chrome_trace(fname)
            with open(fname) as f:
                j = json.load(f)
                op_events = [
                    e
                    for e in j["traceEvents"]
                    if e.get("name", "") == "add_test_kwinputs"
                ]
                self.assertTrue(len(op_events) > 0)
                for e in op_events:
                    args = e["args"]
                    self.assertTrue("stream" in args)
                    self.assertTrue("grid" in args)
                    self.assertTrue("boolean" in args)
                    self.assertTrue(args["stream"] == 0)
                    self.assertTrue(args["grid"] == "lambda x : x + 1")
                    self.assertTrue(args["debug"] == "None")
                    self.assertTrue(args["boolean"])
                    self.assertTrue(e["cat"] == "cpu_op")

        with profile(record_shapes=True) as p1:
            cm = torch._C._profiler._RecordFunctionFast(
                "add_test_kwinputs",
                [x, y],
                {"stream": "test", "grid": [1, 2], "scope": "user_scope"},
            )
            for _ in range(4):
                with cm:
                    x.add(y)
        with TemporaryFileName(mode="w+") as fname1:
            p1.export_chrome_trace(fname1)
            with open(fname1) as f1:
                j = json.load(f1)
                op_events = [
                    e
                    for e in j["traceEvents"]
                    if e.get("name", "") == "add_test_kwinputs"
                ]
                self.assertTrue(len(op_events) > 0)
                for e in op_events:
                    args = e["args"]
                    self.assertTrue("stream" not in args)
                    self.assertTrue("grid" not in args)
                    self.assertTrue(e["cat"] == "user_annotation")