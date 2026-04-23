def _test_all_reduce_coalesced_helper(
            self,
            group,
            group_id,
            rank,
            op,
            cuda=False,
            rank_to_GPU=None,
        ):
            test_case_func = {
                dist.ReduceOp.SUM: self._all_reduce_coalesced_sum_test_cases,
                dist.ReduceOp.PRODUCT: self._all_reduce_coalesced_product_test_cases,
                dist.ReduceOp.MIN: self._all_reduce_coalesced_min_test_cases,
                dist.ReduceOp.MAX: self._all_reduce_coalesced_max_test_cases,
            }[op]

            master_values, worker_values, expected_values, dtypes = test_case_func(
                len(group)
            )

            for src in group:
                curr_values = master_values if rank == src else worker_values
                tensors = [
                    _build_tensor(src + 1, val, dtype=dtype)
                    for dtype, val in zip(dtypes, curr_values, strict=True)
                ]
                if cuda:
                    tensors = [t.cuda(rank_to_GPU[rank][0]) for t in tensors]
                tensor_shapes = []
                for tensor in tensors:
                    if tensor.dtype == torch.complex64:
                        tensor_shapes.append(torch.view_as_real(tensor).shape)
                    else:
                        tensor_shapes.append(tensor.shape)
                self.call_dist_op(
                    ":all_reduce",
                    False,
                    dist.all_reduce_coalesced,
                    tensors,
                    op,
                    group_id,
                    tensor_shapes=tensor_shapes,
                )
                expected_tensors = [
                    _build_tensor(src + 1, expected_value, dtype=dtype)
                    for dtype, expected_value in zip(
                        dtypes, expected_values, strict=True
                    )
                ]
                self.assertEqual(tensors, expected_tensors)

            self._barrier()