def test_python_function_events_in_events(self):
        class DummyModule(nn.Module):
            def forward(self, x):
                return x + 1

        mod = DummyModule()
        with profile(
            activities=[ProfilerActivity.CPU],
            with_stack=True,
            experimental_config=_ExperimentalConfig(verbose=True),
        ) as prof:
            mod(torch.randn(4, 4))

        events = prof.events()
        python_events = [e for e in events if e.is_python_function]
        self.assertGreater(len(python_events), 0)
        for e in python_events:
            self.assertIsInstance(e.name, str)
            self.assertGreater(e.time_range.end - e.time_range.start, 0)

        with TemporaryFileName(mode="w+") as fname:
            prof.export_chrome_trace(fname)
            with open(fname) as f:
                trace = json.load(f)

            json_py = [
                e
                for e in trace["traceEvents"]
                if e.get("cat") == "python_function" and e.get("ph") == "X"
            ]
            self.assertEqual(len(python_events), len(json_py))

            # Verify python_id/parent_id/module_id parity with JSON args
            fe_mod = next((e for e in events if "DummyModule" in e.name), None)
            self.assertIsNotNone(fe_mod)
            self.assertGreater(fe_mod.python_id, 0)
            self.assertGreaterEqual(fe_mod.python_module_id, 0)

            json_mod = next(
                (e for e in json_py if "DummyModule" in e.get("name", "")),
                None,
            )
            self.assertIsNotNone(json_mod)
            args = json_mod["args"]
            self.assertEqual(fe_mod.python_id, args["Python id"])
            self.assertEqual(fe_mod.python_parent_id, args["Python parent id"])
            self.assertEqual(fe_mod.python_module_id, args["Python module id"])