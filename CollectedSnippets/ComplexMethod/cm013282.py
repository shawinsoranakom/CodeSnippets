def _test_all_gather_coalesced_helper(
            self, group, group_id, rank, dtype=torch.float
        ):
            # TODO: Instead we should probably go through _rank_not_in_group
            # mechanism to disable sending tensors
            if group_id is not None:
                for test_case_id in range(2, 5):
                    # Make sure we create tensors of incompatible sizes, e.g.
                    # [1], [2x2], [3x3x3] ... to be sent in one batch
                    input_tensors = [
                        _build_multidim_tensor(
                            tensor_id, tensor_id, rank + tensor_id, dtype=dtype
                        )
                        for tensor_id in range(1, test_case_id)
                    ]
                    output_tensor_lists = [
                        [
                            _build_multidim_tensor(
                                tensor_id, tensor_id, -1, dtype=dtype
                            )
                            for tensor_id in range(1, test_case_id)
                        ]
                        for _ in group
                    ]
                    expected_tensors = [
                        [
                            _build_multidim_tensor(
                                tensor_id, tensor_id, rank_iter + tensor_id, dtype=dtype
                            )
                            for tensor_id in range(1, test_case_id)
                        ]
                        for rank_iter in group
                    ]
                    if not self._run_all_gather_coalesced_and_verify(
                        output_tensor_lists, input_tensors, expected_tensors, group_id
                    ):
                        raise AssertionError(
                            "output tensors do not match expected outputs"
                        )

            self._barrier()