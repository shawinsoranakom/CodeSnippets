def test_reduce_scatter_tensor_coalesced(self):
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
                out_sizes = [5, 10, 15]
                in_sizes = [s * self.world_size for s in out_sizes]

                outputs = [torch.empty(s) for s in out_sizes]
                inputs = []
                for in_size, out_size in zip(in_sizes, out_sizes, strict=True):
                    inp = torch.empty(in_size)
                    for i in range(self.world_size):
                        inp[i * out_size : (i + 1) * out_size] = float(
                            self.rank + i + 1
                        )
                    inputs.append(inp)

                opts = c10d.ReduceScatterOptions()
                opts.reduceOp = op
                work = dist.group.WORLD.reduce_scatter_tensor_coalesced(
                    outputs, inputs, opts
                )
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

                for output, out_size in zip(outputs, out_sizes, strict=True):
                    expect = torch.full((out_size,), expected_val)
                    self.assertTrue(
                        torch.allclose(output, expect),
                        f"op={op}, rank={self.rank}: output={output[0]}, expected={expect[0]}",
                    )