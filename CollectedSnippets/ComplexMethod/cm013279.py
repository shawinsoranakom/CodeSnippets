def _test_scatter_helper(
            self, group, group_id, rank, cuda=False, rank_to_GPU=None, dtype=torch.float
        ):
            for dest in group:
                tensor = _build_tensor(dest + 1, -1, dtype=dtype)
                expected_tensor = _build_tensor(dest + 1, rank, dtype=dtype)
                tensors = (
                    [_build_tensor(dest + 1, i, dtype=dtype) for i in group]
                    if rank == dest
                    else []
                )
                if cuda:
                    tensor = tensor.cuda(rank_to_GPU[rank][0])
                    tensors = [t.cuda(rank_to_GPU[rank][0]) for t in tensors]
                if dtype == torch.complex64:
                    tensor_shapes = [torch.view_as_real(t).shape for t in tensors]
                else:
                    tensor_shapes = [t.shape for t in tensors]
                self.call_dist_op(
                    ":scatter",
                    False,
                    dist.scatter,
                    tensor,
                    src=dest,
                    scatter_list=tensors,
                    group=group_id,
                    expect_event=False,
                    tensor_shapes=tensor_shapes,
                )
                self.assertEqual(tensor, expected_tensor)

            self._barrier()