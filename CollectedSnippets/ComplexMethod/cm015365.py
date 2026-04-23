def _test_collectives_op_mismatch(self, wrapper_pg, use_accel=False):
        tensor = torch.randn(20, 10)
        if use_accel:
            tensor = tensor.to(self.rank)
        works = []
        # Run a few successful collectives
        for _ in range(500):
            work = wrapper_pg.allreduce([tensor])
            works.append(work)

        for w in works:
            w.wait()

        # Simulate mismatch: allreduce vs reduce.
        # Error including info about inconsistent collective, rank, tensor
        # shape, device, and dtype should be raised.
        with self.assertRaisesRegex(RuntimeError, ".*") as cm:
            if self.rank == 0:
                wrapper_pg.allreduce([tensor])
            else:
                wrapper_pg.reduce([tensor])
        self._validate_error(
            exception=cm.exception,
            op_type="ALLREDUCE" if self.rank == 0 else "REDUCE",
            rank=self.rank,
            tensor=tensor,
        )

        with self.assertRaisesRegex(RuntimeError, ".*") as cm:
            if self.rank == 0:
                wrapper_pg.reduce([tensor])
            else:
                wrapper_pg.barrier()
        self._validate_error(
            exception=cm.exception,
            op_type="REDUCE" if self.rank == 0 else "BARRIER",
            rank=self.rank,
            tensor=tensor,
        )

        with self.assertRaisesRegex(RuntimeError, ".*") as cm:
            if self.rank == 0:
                wrapper_pg.broadcast(tensor, 0)
            else:
                output_tensors = [
                    torch.zeros_like(tensor) for _ in range(self.world_size)
                ]
                wrapper_pg.allgather([output_tensors], [tensor])
        self._validate_error(
            exception=cm.exception,
            op_type="BROADCAST" if self.rank == 0 else "ALLGATHER",
            rank=self.rank,
            tensor=tensor,
        )