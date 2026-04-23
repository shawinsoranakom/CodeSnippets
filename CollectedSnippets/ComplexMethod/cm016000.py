def test_profiler_op_args_events_parity(self):
        """Verify that cpu_op args on events() match Chrome trace JSON args."""
        base_tensor = torch.randn(1024, dtype=torch.float32)
        a = base_tensor.as_strided((16, 16), (17, 1), 0)
        b = base_tensor.as_strided((16, 16), (25, 2), 272)
        t1 = torch.ones((64, 32))
        t2 = torch.ones((64, 32))
        with profile(activities=[ProfilerActivity.CPU], record_shapes=True) as prof:
            torch.add(a, b)
            torch.cat([t1, t2])

        fe_add = next((e for e in prof.events() if e.name == "aten::add"), None)
        self.assertIsNotNone(fe_add)
        fe_cat = next((e for e in prof.events() if e.name == "aten::cat"), None)
        self.assertIsNotNone(fe_cat)

        with TemporaryFileName(mode="w+") as fname:
            prof.export_chrome_trace(fname)
            with open(fname) as f:
                j = json.load(f)

            json_add = next(
                (
                    e
                    for e in j["traceEvents"]
                    if e.get("name") == "aten::add" and e.get("cat") == "cpu_op"
                ),
                None,
            )
            self.assertIsNotNone(json_add)
            args = json_add["args"]
            self.assertEqual(fe_add.structured_input_shapes, args["Input Dims"])
            self.assertEqual(fe_add.structured_input_strides, args["Input Strides"])
            self.assertEqual(fe_add.input_dtypes, args["Input type"])

            # Test a case with TensorList inputs -- structured_input_shapes
            # should handle TensorList nesting correctly.
            json_cat = next(
                (
                    e
                    for e in j["traceEvents"]
                    if e.get("name") == "aten::cat" and e.get("cat") == "cpu_op"
                ),
                None,
            )
            self.assertIsNotNone(json_cat)
            args_cat = json_cat["args"]
            self.assertEqual(fe_cat.structured_input_shapes, args_cat["Input Dims"])
            self.assertEqual(fe_cat.structured_input_strides, args_cat["Input Strides"])
            self.assertEqual(fe_cat.input_dtypes, args_cat["Input type"])