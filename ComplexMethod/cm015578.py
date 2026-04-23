def test_distribute_tensor_rank(self):
        comm_mode = CommDebugMode()

        device_mesh = self.build_device_mesh()
        shard_spec = [Shard(0)]

        for requires_grad in [True, False]:
            tensor_to_shard = torch.randn(
                3 * self.world_size, 3, requires_grad=requires_grad
            )
            with comm_mode:
                dist_tensor = distribute_tensor(
                    tensor_to_shard, device_mesh, shard_spec
                )
                self.assertEqual(comm_mode.get_comm_counts()[c10d_ops.scatter_], 1)
            self.assertEqual(dist_tensor.size(), torch.Size([3 * self.world_size, 3]))
            local_tensor = dist_tensor.to_local()
            self.assertEqual(local_tensor.size(), torch.Size([3, 3]))
            if requires_grad:
                self.assertTrue(dist_tensor.requires_grad)
                self.assertTrue(dist_tensor.is_leaf)

        # test negative dim
        shard_minus_spec = [Shard(-1)]
        tensor_to_shard = torch.randn(3, 3 * self.world_size)
        dist_tensor = distribute_tensor(tensor_to_shard, device_mesh, shard_minus_spec)
        self.assertEqual(dist_tensor.placements[0].dim, 1)

        placement_combs = [
            [Shard(0)],
            [Shard(1)],
            [Replicate()],
            [Partial(reduce_op="sum")],
            [Partial(reduce_op="avg")],
        ]

        if not self.is_local_tensor_enabled:
            # test src_data_rank == 1
            # set seed differently for each rank
            self.init_manual_seed_for_rank()
            for placement in placement_combs:
                tensor_to_distribute = torch.randn(
                    3 * self.world_size, 3 * self.world_size
                )
                dtensor = distribute_tensor(
                    tensor_to_distribute, device_mesh, placement, src_data_rank=1
                )
                full_dtensor = dtensor.full_tensor()
                if self.rank == 1:
                    self.assertEqual(full_dtensor, tensor_to_distribute)

        # test src_data_rank = None, make sure it does not have communication
        with comm_mode:
            for placement in placement_combs:
                if isinstance(placement[0], Shard):
                    shard_dim = placement[0].dim
                    shape = [3, 3]
                    shape[shard_dim] *= self.world_size
                    tensor_to_distribute = torch.randn(*shape)
                else:
                    tensor_to_distribute = torch.randn(3, 3)

                dtensor = distribute_tensor(
                    tensor_to_distribute, device_mesh, placement, src_data_rank=None
                )
                self.assertEqual(dtensor.to_local().shape, (3, 3))
        self.assertEqual(comm_mode.get_total_counts(), 0)