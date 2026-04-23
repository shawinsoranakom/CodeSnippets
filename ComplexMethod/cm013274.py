def _test_broadcast_helper(
            self,
            group,
            group_id,
            rank,
            cuda=False,
            rank_to_GPU=None,
            with_options=False,
        ):
            for dtype, value, requires_cuda in [
                (torch.float, -1e-10, False),
                (torch.double, -1e-100, False),
                (torch.half, -0.1, True),
                (torch.int8, -2, False),
                (torch.uint8, 129, False),
                (torch.int, -1e5, False),
                (torch.long, -1e15, False),
            ]:
                if requires_cuda and not cuda:
                    continue
                for src in group:
                    expected_tensor = _build_tensor(src + 1, value, dtype)
                    if cuda:
                        expected_tensor = expected_tensor.cuda(rank_to_GPU[rank][0])
                    if rank == src:
                        if with_options:
                            opts = dist.BroadcastOptions()
                            opts.rootTensor = 0
                            opts.rootRank = src
                            self.call_dist_op(
                                ":broadcast",
                                True,
                                group_id.broadcast,
                                [expected_tensor],
                                opts,
                            )
                        else:
                            self.call_dist_op(
                                ":broadcast",
                                False,
                                dist.broadcast,
                                expected_tensor,
                                src,
                                group_id,
                            )
                    else:
                        tensor = _build_tensor(src + 1, -1, dtype)
                        if cuda:
                            tensor = tensor.cuda(rank_to_GPU[rank][0])
                        if with_options:
                            opts = dist.BroadcastOptions()
                            opts.rootTensor = 0
                            opts.rootRank = src
                            self.call_dist_op(
                                ":broadcast", True, group_id.broadcast, [tensor], opts
                            )
                        else:
                            self.call_dist_op(
                                ":broadcast",
                                False,
                                dist.broadcast,
                                tensor,
                                src,
                                group_id,
                            )
                        self.assertEqual(tensor.size(), expected_tensor.size())
                        self.assertEqual(
                            tensor.ne(expected_tensor).max(), torch.tensor(False)
                        )

            self._barrier()