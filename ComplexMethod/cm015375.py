def _test_allgather_basics(self, fn):
        store = c10d.FileStore(self.file_name, self.world_size)
        pg = self._create_process_group_gloo(
            store, self.rank, self.world_size, self.opts()
        )

        # Run with N input tensor per rank
        for n in [1, 2, 3]:
            input = [fn(torch.tensor([n * self.rank + i])) for i in range(n)]
            output = [
                [fn(torch.tensor([-1])) for _ in range(n * self.world_size)]
                for _ in range(n)
            ]
            expected_output = [
                [fn(torch.tensor([i])) for i in range(n * self.world_size)]
                for _ in range(n)
            ]
            fut = pg.allgather(output, input).get_future()
            fut.wait()
            result = fut.value()
            if n == 1:
                result = [result]
            self.assertEqual(expected_output, result)