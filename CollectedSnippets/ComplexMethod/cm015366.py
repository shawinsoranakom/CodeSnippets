def _test_collective_shape_mismatch(self, wrapper_pg, use_accel=False):
        wrapper_pg.barrier()
        dim = 2 if self.rank == 0 else 10
        tensor = torch.randn(20, dim)
        if use_accel:
            tensor = tensor.to(self.rank)
        with self.assertRaisesRegex(RuntimeError, ".*") as cm:
            wrapper_pg.allreduce([tensor])
        self._validate_error(
            exception=cm.exception,
            op_type="ALLREDUCE",
            rank=self.rank,
            tensor=tensor,
        )

        # Check errors are raised when dimensionality of shapes is different
        tensor = torch.randn(20, 10, 2) if self.rank == 0 else torch.randn(20, 10)
        if use_accel:
            tensor = tensor.to(self.rank)
        with self.assertRaisesRegex(RuntimeError, ".*") as cm:
            wrapper_pg.allreduce([tensor])
        self._validate_error(
            exception=cm.exception,
            op_type="ALLREDUCE",
            rank=self.rank,
            tensor=tensor,
        )

        # Check shape errors with scatter
        input = [
            torch.tensor(
                [self.rank] if self.rank == 0 else [self.rank, self.rank],
                device=self.rank if use_accel else "cpu",
            )
            for _ in range(self.world_size)
        ]
        outputs = [
            torch.tensor(
                [-1] if self.rank == 0 else [-1, -1],
                device=self.rank if use_accel else "cpu",
            )
            for _ in range(self.world_size)
        ]
        root_rank = 0
        opts = c10d.ScatterOptions()
        opts.rootRank = root_rank
        with self.assertRaisesRegex(RuntimeError, ".*") as cm:
            if self.rank == root_rank:
                wrapper_pg.scatter([outputs[self.rank]], [input], opts).wait()
            else:
                wrapper_pg.scatter([outputs[self.rank]], [], opts).wait()
        self._validate_error(
            exception=cm.exception,
            op_type="SCATTER",
            rank=self.rank,
            tensor=outputs[self.rank],
        )