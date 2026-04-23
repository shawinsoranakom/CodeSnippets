def _test_alltoall_multidim(self, fn):
        """Test alltoall with multi-dimensional tensors."""
        store = c10d.FileStore(self.file_name, self.world_size)
        pg = self._create_process_group_gloo(
            store, self.rank, self.world_size, self.opts()
        )

        # Each rank sends a 3x4 tensor with unique values to each destination
        # Value pattern: rank * 1000 + dest * 100 + row * 10 + col
        input_tensors = []
        for dest in range(self.world_size):
            t = torch.zeros(3, 4, dtype=torch.float32)
            for row in range(3):
                for col in range(4):
                    t[row, col] = self.rank * 1000 + dest * 100 + row * 10 + col
            input_tensors.append(fn(t))

        output_tensors = [
            fn(torch.zeros(3, 4, dtype=torch.float32)) for _ in range(self.world_size)
        ]

        fut = pg.alltoall(output_tensors, input_tensors).get_future()
        fut.wait()

        # Verify: output_tensors[src] should contain what rank src sent to us
        for src in range(self.world_size):
            expected = torch.zeros(3, 4, dtype=torch.float32)
            for row in range(3):
                for col in range(4):
                    expected[row, col] = src * 1000 + self.rank * 100 + row * 10 + col
            self.assertEqual(expected, output_tensors[src].cpu())