def _test_all_to_all_helper(
            self,
            group,
            group_id,
            rank,
            cuda=False,
            rank_to_GPU=None,
            dtype=torch.float,
        ):
            if group_id is not None:
                size = len(group)
                in_splits = [i + 1 for i in group]
                in_tensors = [
                    torch.ones([in_splits[i], size], dtype=dtype) * rank
                    for i, _ in enumerate(group)
                ]
                out_tensors = [
                    torch.ones([(rank + 1), size], dtype=dtype) for _ in group
                ]
                expected_tensors = [
                    torch.ones([rank + 1, size], dtype=dtype) * i for i in group
                ]
                if cuda:
                    in_tensors = [t.cuda(rank_to_GPU[rank][0]) for t in in_tensors]
                    expected_tensors = [
                        t.cuda(rank_to_GPU[rank][0]) for t in expected_tensors
                    ]
                    out_tensors = [t.cuda(rank_to_GPU[rank][0]) for t in out_tensors]
                dist.all_to_all(out_tensors, in_tensors, group=group_id)
                for t1, t2 in zip(out_tensors, expected_tensors, strict=True):
                    self.assertEqual(t1, t2)
            self._barrier()