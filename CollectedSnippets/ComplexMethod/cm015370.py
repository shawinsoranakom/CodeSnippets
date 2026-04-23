def test_reduce_scatter(self):
        store = c10d.FileStore(self.file_name, self.world_size)
        dist.init_process_group(
            backend="gloo",
            store=store,
            rank=self.rank,
            world_size=self.world_size,
        )
        torch.manual_seed(42)

        for op in (
            c10d.ReduceOp.SUM,
            c10d.ReduceOp.AVG,
            c10d.ReduceOp.MIN,
            c10d.ReduceOp.MAX,
            c10d.ReduceOp.PRODUCT,
        ):
            with self.subTest(op=op):
                inputs = [
                    torch.full((3,), float(self.rank + i + 1))
                    for i in range(self.world_size)
                ]
                output = torch.empty(3)

                work = dist.reduce_scatter(output, inputs, op=op, async_op=True)
                work.wait()

                r = self.rank
                ws = self.world_size
                values = [float(r + k + 1) for k in range(ws)]

                if op == c10d.ReduceOp.SUM:
                    expected_val = sum(values)
                elif op == c10d.ReduceOp.AVG:
                    expected_val = sum(values) / ws
                elif op == c10d.ReduceOp.MIN:
                    expected_val = min(values)
                elif op == c10d.ReduceOp.MAX:
                    expected_val = max(values)
                elif op == c10d.ReduceOp.PRODUCT:
                    expected_val = reduce(operator.mul, values, 1.0)
                else:
                    raise ValueError(f"Unsupported op: {op}")

                expect = torch.full((3,), expected_val)
                self.assertTrue(
                    torch.allclose(output, expect),
                    f"op={op}, rank={self.rank}: output={output}, expected={expect}",
                )