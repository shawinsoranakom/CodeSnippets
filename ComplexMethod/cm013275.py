def _test_reduce_twice_helper(
            self,
            group,
            group_id,
            rank,
            op,
            master_value,
            worker_value,
            expected_value,
            cuda=False,
            rank_to_GPU=None,
        ):
            for src in group:
                tensors = [
                    _build_tensor(src + 1).fill_(
                        master_value if rank == src else worker_value
                    )
                    for i in range(2)
                ]
                if cuda:
                    for i in range(2):
                        tensors[i] = tensors[i].cuda(rank_to_GPU[rank][0])
                self.call_dist_op(
                    ":reduce",
                    False,
                    dist.reduce,
                    tensors[0],
                    src,
                    op,
                    group_id,
                    secondary_op_call=lambda: dist.reduce(
                        tensors[1], src, op, group_id
                    ),
                    tensor_shapes=[tensors[0].shape],
                )
                if rank == src:
                    for tensor in tensors:
                        self.assertEqual(tensor, _build_tensor(src + 1, expected_value))

            self._barrier()