def _test_allgather_basics(self, fn):
        pg = self._create_process_group_ucc()

        # TODO: Run with N input tensor per rank; for now, UCC only supports single tensor input so N=1
        for n in [1]:
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