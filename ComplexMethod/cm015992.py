def test_profiler_op_event_kwargs_list_of_strings(self):
        x, y = (torch.rand((4, 4)) for _ in range(2))
        with profile(record_shapes=True) as p:
            cm = torch._C._profiler._RecordFunctionFast(
                "add_test_kwinputs_string_list",
                [x, y],
                {
                    "string_list": ["hello", "world", "test"],
                    "int_param": 42,
                    "string_param": "single_string",
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
                    if e.get("name", "") == "add_test_kwinputs_string_list"
                ]
                self.assertTrue(len(op_events) > 0)
                for e in op_events:
                    args = e["args"]
                    self.assertTrue("string_list" in args)
                    self.assertTrue("int_param" in args)
                    self.assertTrue("string_param" in args)
                    # Check that the list of strings is properly serialized
                    # The list should be formatted as a JSON array by ivalueListToStr
                    self.assertEqual(args["string_list"], ["hello", "world", "test"])
                    self.assertEqual(args["int_param"], 42)
                    self.assertEqual(args["string_param"], "single_string")
                    self.assertTrue(e["cat"] == "cpu_op")

        # Test mixed types that should be filtered out
        with profile(record_shapes=True) as p1:
            cm = torch._C._profiler._RecordFunctionFast(
                "add_test_kwinputs_string_list_filtered",
                [x, y],
                {
                    "valid_string_list": ["valid1", "valid2"],
                    "mixed_list": ["string", 123],  # Should be filtered out
                    "non_string_list": [1, 2, 3],  # Should be filtered out
                    "valid_int": 100,
                },
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
                    if e.get("name", "") == "add_test_kwinputs_string_list_filtered"
                ]
                self.assertTrue(len(op_events) > 0)
                for e in op_events:
                    args = e["args"]
                    # Only valid types should be present
                    self.assertTrue("valid_string_list" in args)
                    self.assertTrue("valid_int" in args)
                    # Invalid lists should be filtered out
                    self.assertTrue("mixed_list" not in args)
                    self.assertTrue("non_string_list" not in args)
                    # Check values
                    self.assertEqual(args["valid_string_list"], ["valid1", "valid2"])
                    self.assertEqual(args["valid_int"], 100)
                    self.assertTrue(e["cat"] == "cpu_op")