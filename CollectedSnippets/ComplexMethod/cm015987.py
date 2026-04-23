def test_module_hierarchy(self):
        class A(nn.Module):
            def my_new_method(self, x):
                return x * 3

            def forward_impl_(self, x, y):
                return self.my_new_method(x) + y

            def forward(self, x, y):
                y = y - 2
                return self.forward_impl_(x, y)

        class B(nn.Module):
            def forward(self, x):
                return x + 2

        class C(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.A0 = A()
                self.B0 = B()

            def call_b(self, x):
                return self.B0.forward(x)

            def forward(self, x, y):
                return self.A0.forward(x, y) + self.call_b(x)

        model = C()
        model = torch.jit.script(model)
        input_a = torch.rand(128, 128)
        input_b = torch.rand(128, 128)
        op_to_module_hierarchy = {}
        op_to_module_hierarchy["aten::sub"] = ["TOP(C)::forward.A0(A)::forward."]
        op_to_module_hierarchy["aten::mul"] = [
            "TOP(C)::forward.A0(A)::forward.SELF(A)::forward_impl_.SELF(A)::my_new_method."
        ]
        op_to_module_hierarchy["aten::add"] = [
            "TOP(C)::forward.A0(A)::forward.SELF(A)::forward_impl_.",
            "TOP(C)::forward.SELF(C)::call_b.B0(B)::forward.",
            "TOP(C)::forward.",
        ]
        with TemporaryFileName(mode="w+") as fname:
            with profile(
                activities=[torch.profiler.ProfilerActivity.CPU],
                with_modules=True,
            ) as prof:
                model(input_a, input_b)
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
                    if "args" in evt:
                        op_name = evt["name"]
                        if "Module Hierarchy" in evt["args"]:
                            hierarchy = evt["args"]["Module Hierarchy"]
                            if op_name in op_to_module_hierarchy:
                                if hierarchy not in op_to_module_hierarchy[op_name]:
                                    raise AssertionError(
                                        f"Expected hierarchy '{hierarchy}' in {op_to_module_hierarchy[op_name]}"
                                    )