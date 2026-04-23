def test_runtime_estimates_simple(self):
        """Test runtime estimates logging with simple compute and collective ops."""
        import torch.distributed as dist

        store = FakeStore()
        dist.init_process_group(backend="fake", rank=0, world_size=2, store=store)

        class SimpleModule(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = torch.nn.Linear(4, 4)

            def forward(self, x):
                h = self.linear(x)
                h = torch.relu(h)

                h = torch.ops._c10d_functional.all_reduce.default(h, "sum", "0")
                h = torch.ops._c10d_functional.wait_tensor.default(h)
                return h

        try:
            with self._setup_runtime_estimates_capture() as payload_buffer:
                torch._dynamo.reset()

                mod = SimpleModule().cuda()
                compiled = torch.compile(mod, backend="inductor")
                compiled(torch.randn(4, 4, device="cuda"))

                # Verify runtime + tensor meta artifact was logged
                self.assertIn(
                    '"inductor_runtime_and_tensor_meta"', self.buffer.getvalue()
                )

                payload_content = payload_buffer.getvalue().strip()
                if payload_content:
                    data = json.loads(payload_content)
                    self.assertIn("ops", data)
                    ops = data["ops"]

                    # Verify runtime estimates
                    compute_ops = [op for op in ops if op["type"] == "compute"]
                    collective_ops = [op for op in ops if op["type"] == "collective"]

                    self.assertTrue(len(compute_ops) > 0 or len(collective_ops) > 0)

                    # Just check each op has an estimated runtime value (any value, including 0)
                    for op in ops:
                        self.assertIn("estimated_runtime_ns", op)
                        self.assertIsNotNone(op["estimated_runtime_ns"])

                self.assertParses()
        finally:
            dist.destroy_process_group()