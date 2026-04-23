def _test_scatter_stress(self, inputs, fn):
        store = c10d.FileStore(self.file_name, self.world_size)
        pg = self._create_process_group_gloo(
            store, self.rank, self.world_size, self.opts(threads=8)
        )
        outputs = [
            [fn(torch.tensor([-1])) for _ in range(self.world_size)]
            for _ in range(len(inputs))
        ]
        future_handles = []
        for i in range(len(inputs)):
            for root in range(self.world_size):
                opts = c10d.ScatterOptions()
                opts.rootRank = root
                if root == self.rank:
                    fut = pg.scatter(
                        [outputs[i][root]], [[fn(e) for e in inputs[i]]], opts
                    ).get_future()
                else:
                    fut = pg.scatter([outputs[i][root]], [], opts).get_future()
                future_handles.append(fut)

        for i, future_handle in enumerate(future_handles):
            future_handle.wait()
            iter = i // self.world_size
            root = i % self.world_size
            result = future_handle.value()

            self.assertEqual(
                torch.tensor([iter + root]),
                result[0],
                msg=(f"Mismatch in iteration {iter:d} for rank {root:d}"),
            )