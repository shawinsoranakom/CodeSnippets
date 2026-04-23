def test_reduce_ops(self):
        pg = self.pg
        local_device_id = self.rank_to_GPU[self.rank][0]

        def reduce(xs, rootRank, rootTensor, op=None):
            opts = c10d.ReduceOptions()
            opts.rootRank = rootRank
            opts.rootTensor = rootTensor
            if op:
                opts.reduceOp = op
            work = pg.reduce(xs, opts)
            work.wait()

        # for every root tensor
        for rt in range(self.world_size):
            tensors = [torch.tensor([self.rank + 1]).cuda(local_device_id)]

            reduce(tensors, rt, 0)

            if self.rank == rt:
                self.assertEqual(
                    torch.tensor([self.world_size * (self.world_size + 1) // 2]),
                    tensors[0],
                )
            else:
                self.assertEqual(
                    torch.tensor([self.rank + 1]),
                    tensors[0],
                )

            for op, err in zip(
                (c10d.ReduceOp.BAND, c10d.ReduceOp.BOR, c10d.ReduceOp.BXOR),
                ("ReduceOp.BAND", "ReduceOp.BOR", "ReduceOp.BXOR"),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Cannot use " + err + " with NCCL"
                ):
                    reduce(tensors, self.rank, rt, op)

            # Premul sum
            if torch.cuda.nccl.version() >= (2, 11, 1):
                for factor in (3.0, torch.tensor([5.0], device=local_device_id)):
                    if isinstance(factor, torch.Tensor):
                        factor_ref = factor.cpu().item()
                    else:
                        factor_ref = factor
                    float_tensors = [
                        torch.tensor(
                            [self.rank + 1.0], device=f"cuda:{local_device_id}"
                        )
                    ]
                    float_tensors_ref = [
                        torch.tensor(
                            [(self.rank + 1.0) * factor_ref],
                            device=f"cuda:{local_device_id}",
                        )
                    ]

                    reduce(float_tensors_ref, rt, 0)
                    reduce(float_tensors, rt, 0, c10d._make_nccl_premul_sum(factor))
                    if self.rank == rt:
                        self.assertEqual(float_tensors_ref[0], float_tensors[0])