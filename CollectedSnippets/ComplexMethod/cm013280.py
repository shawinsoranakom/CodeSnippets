def _test_gather_helper(
            self, group, group_id, rank, cuda=False, rank_to_GPU=None
        ):
            for dest in group:
                tensor = _build_tensor(dest + 1, rank)
                tensors = (
                    [_build_tensor(dest + 1, -1) for i in group] if rank == dest else []
                )
                if cuda:
                    tensor = tensor.cuda(rank_to_GPU[rank][0])
                    tensors = [t.cuda(rank_to_GPU[rank][0]) for t in tensors]
                self.call_dist_op(
                    ":gather",
                    False,
                    dist.gather,
                    tensor,
                    dst=dest,
                    gather_list=tensors,
                    group=group_id,
                    expect_event=False,
                    tensor_shapes=[tensors[0].shape] if len(tensors) > 0 else None,
                )
                if rank == dest:
                    expected_tensors = [_build_tensor(dest + 1, i) for i in group]
                    for t1, t2 in zip(tensors, expected_tensors, strict=True):
                        self.assertEqual(t1, t2)

            self._barrier()