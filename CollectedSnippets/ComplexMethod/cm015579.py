def test_nll_loss_and_cross_entropy(self):
        device_mesh = self.build_device_mesh()
        comm_mode = CommDebugMode()

        channel_size, channel_dim = 16, 1
        test_setup = [
            (2, (8, channel_size), (8,)),  # calling aten.nll_loss_forward
            (3, (8, channel_size, 12), (8, 12)),  # calling aten.nll_loss2d_forward
        ]
        for input_ndim, input_size, target_size in test_setup:
            x = torch.rand(*input_size, device=self.device_type, requires_grad=True)
            target = torch.randint(channel_size, target_size, device=self.device_type)
            dist_target = distribute_tensor(target, device_mesh, [Replicate()])

            shard_dims = list(range(input_ndim))
            reductions = ["none", "mean", "sum"]
            # Compared with nll_loss, cross_entropy additionally calls log_softmax first.
            # Testing them together as code can be reused.
            loss_functions = [
                torch.nn.functional.nll_loss,
                torch.nn.functional.cross_entropy,
            ]
            for shard_dim, reduction, loss_fn in itertools.product(
                shard_dims, reductions, loss_functions
            ):
                dist_x = distribute_tensor(x, device_mesh, [Shard(shard_dim)])
                y = loss_fn(x, target, reduction=reduction)
                if reduction == "none":
                    y.sum().backward()
                else:
                    y.backward()
                with comm_mode:
                    dist_y = loss_fn(dist_x, dist_target, reduction=reduction)
                    if shard_dim == channel_dim:
                        self.assertEqual(comm_mode.get_total_counts(), 1)
                        self.assertEqual(
                            comm_mode.get_comm_counts()[funcol.all_gather_into_tensor],
                            1,
                        )
                        self.assertTrue(dist_y.placements[0].is_replicate())
                        self.assertEqual(dist_y.to_local(), y)
                    else:
                        self.assertEqual(comm_mode.get_total_counts(), 0)
                        if reduction == "none":
                            output_shard_dim = (
                                shard_dim if shard_dim < channel_dim else shard_dim - 1
                            )
                            self.assertTrue(
                                dist_y.placements[0].is_shard(dim=output_shard_dim)
                            )
                        else:
                            self.assertTrue(dist_y.placements[0].is_partial())
                        self.assertEqual(dist_y.full_tensor(), y)

                    if reduction == "none":
                        dist_y.sum().backward()
                    else:
                        dist_y.backward()
                    if shard_dim == channel_dim:
                        self.assertTrue(dist_x.grad.placements[0].is_replicate())
                        self.assertEqual(dist_x.grad.to_local(), x.grad)
                    else:
                        self.assertTrue(
                            dist_x.grad.placements[0].is_shard(dim=shard_dim)
                        )
                        self.assertEqual(dist_x.grad.full_tensor(), x.grad)
                    x.grad.zero_()