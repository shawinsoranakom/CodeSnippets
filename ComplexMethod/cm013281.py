def _test_all_gather_helper(
            self, group, group_id, rank, cuda=False, rank_to_GPU=None, dtype=torch.float
        ):
            for dest in group:
                tensor = _build_tensor(dest + 1, rank, dtype=dtype)
                tensors = [_build_tensor(dest + 1, -1, dtype=dtype) for i in group]
                allgather = dist.all_gather
                if cuda:
                    tensor = tensor.cuda(rank_to_GPU[rank][0])
                    tensors = [t.cuda(rank_to_GPU[rank][0]) for t in tensors]
                if tensors[0].dtype == torch.complex64:
                    tensor_shapes = [torch.view_as_real(tensors[0]).shape]
                else:
                    tensor_shapes = [tensors[0].shape]
                self.call_dist_op(
                    ":all_gather",
                    False,
                    allgather,
                    tensors,
                    tensor,
                    group_id,
                    False,
                    tensor_shapes=tensor_shapes,
                )

                expected_tensors = [
                    _build_tensor(dest + 1, i, dtype=dtype) for i in group
                ]
                for t1, t2 in zip(tensors, expected_tensors, strict=True):
                    self.assertEqual(t1, t2)

            self._barrier()