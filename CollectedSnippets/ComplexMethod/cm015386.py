def test_reduce_op_premul_sum(self):
        if torch.cuda.nccl.version() < (2, 11, 1):
            self.skipTest("NCCL 2.11.1+ is required for PREMUL_SUM")

        pg = self.pg
        local_device_id = self.rank_to_GPU[self.rank][0]

        def allreduce(tensors, op):
            opts = c10d.AllreduceOptions()
            opts.reduceOp = op
            work = pg.allreduce(tensors, opts)
            work.wait()

        def reduce(tensors, op, root=0):
            opts = c10d.ReduceOptions()
            opts.reduceOp = op
            opts.rootRank = root
            work = pg.reduce(tensors, opts)
            work.wait()

        def reduce_scatter(output, input_lists, op):
            opts = c10d.ReduceScatterOptions()
            opts.reduceOp = op
            work = pg.reduce_scatter(output, input_lists, opts)
            work.wait()

        # allreduce
        for dtype in (torch.half, torch.float, torch.double):
            scalar_factor = 3.0
            tensors = [
                torch.tensor([self.rank + 1]).cuda(local_device_id).to(dtype=dtype)
            ]

            allreduce(tensors, c10d.ReduceOp.PREMUL_SUM(scalar_factor))

            expected = scalar_factor * torch.tensor(
                [self.world_size * (self.world_size + 1) / 2],
                dtype=dtype,
                device=f"cuda:{local_device_id}",
            )
            self.assertEqual(expected, tensors[0])

        for dtype in (torch.half, torch.float, torch.double):
            tensor_factor = torch.tensor(
                [5.0], device=f"cuda:{local_device_id}", dtype=dtype
            )
            tensors = [
                torch.tensor([self.rank + 1]).cuda(local_device_id).to(dtype=dtype)
            ]

            allreduce(tensors, c10d.ReduceOp.PREMUL_SUM(tensor_factor))

            expected = tensor_factor * torch.tensor(
                [self.world_size * (self.world_size + 1) / 2],
                dtype=dtype,
                device=f"cuda:{local_device_id}",
            )
            self.assertEqual(expected, tensors[0])

        #  reduce
        for root in range(self.world_size):
            for dtype in (torch.half, torch.float, torch.double):
                # Test with scalar factor
                scalar_factor = 2.0
                tensors = [
                    torch.tensor([self.rank + 1]).cuda(local_device_id).to(dtype=dtype)
                ]

                reduce(tensors, c10d.ReduceOp.PREMUL_SUM(scalar_factor), root)

                if self.rank == root:
                    expected = scalar_factor * torch.tensor(
                        [self.world_size * (self.world_size + 1) / 2],
                        dtype=dtype,
                        device=f"cuda:{local_device_id}",
                    )
                    self.assertEqual(expected, tensors[0])

                # Test with tensor factor
                tensor_factor = torch.tensor(
                    [4.0], device=f"cuda:{local_device_id}", dtype=dtype
                )
                tensors = [
                    torch.tensor([self.rank + 1]).cuda(local_device_id).to(dtype=dtype)
                ]

                reduce(tensors, c10d.ReduceOp.PREMUL_SUM(tensor_factor), root)

                if self.rank == root:
                    expected = tensor_factor * torch.tensor(
                        [self.world_size * (self.world_size + 1) / 2],
                        dtype=dtype,
                        device=f"cuda:{local_device_id}",
                    )
                    self.assertEqual(expected, tensors[0])

        #  reduce_scatter
        for dtype in (torch.half, torch.float, torch.double):
            # Test with scalar factor
            scalar_factor = 3.0
            output = [torch.zeros(1, dtype=dtype, device=f"cuda:{local_device_id}")]
            input_lists = [
                [
                    torch.tensor([i + 1], dtype=dtype, device=f"cuda:{local_device_id}")
                    for i in range(self.world_size)
                ]
            ]

            reduce_scatter(output, input_lists, c10d.ReduceOp.PREMUL_SUM(scalar_factor))

            # Each rank receives sum of (rank+1) from all processes, multiplied by factor
            expected = scalar_factor * torch.tensor(
                [self.world_size * (self.rank + 1)],
                dtype=dtype,
                device=f"cuda:{local_device_id}",
            )
            self.assertEqual(expected, output[0])

            # Test with tensor factor
            tensor_factor = torch.tensor(
                [5.0], device=f"cuda:{local_device_id}", dtype=dtype
            )
            output = [torch.zeros(1, dtype=dtype, device=f"cuda:{local_device_id}")]
            input_lists = [
                [
                    torch.tensor([i + 1], dtype=dtype, device=f"cuda:{local_device_id}")
                    for i in range(self.world_size)
                ]
            ]

            reduce_scatter(output, input_lists, c10d.ReduceOp.PREMUL_SUM(tensor_factor))

            expected = tensor_factor * torch.tensor(
                [self.world_size * (self.rank + 1)],
                dtype=dtype,
                device=f"cuda:{local_device_id}",
            )
            self.assertEqual(expected, output[0])

        # Test that PREMUL_SUM is callable and returns a ReduceOp
        premul_op = c10d.ReduceOp.PREMUL_SUM(2.0)
        self.assertIsInstance(premul_op, c10d.ReduceOp)

        # Test equality comparison
        premul_op1 = c10d.ReduceOp.PREMUL_SUM(2.0)
        premul_op2 = c10d.ReduceOp.PREMUL_SUM(2.0)
        self.assertEqual(premul_op1, premul_op2)

        # Like other ReduceOps, PREMUL_SUM should have a unique integer value.
        self.assertEqual(c10d.ReduceOp.PREMUL_SUM, 8)