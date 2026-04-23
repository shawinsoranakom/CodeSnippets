def test_dtensor_unflatten_1d(self):
        mesh: DeviceMesh = init_device_mesh(self.device_type, (self.world_size,))

        # flatten -> view -> unflatten
        for tensor_ndim in [2, 3, 4]:
            for flatten_start in range(tensor_ndim):
                for flatten_end in range(flatten_start + 2, tensor_ndim + 1):
                    for shard_dim in range(flatten_start, flatten_end):
                        expected_placements = (Shard(shard_dim),)
                        for (
                            tensor_dims_unflatten,
                            local_tensor_dims_unflatten,
                            tensor_dims_flatten,
                        ) in self.generate_tensor_dims_1d(
                            tensor_ndim, flatten_start, flatten_end, shard_dim, mesh
                        ):
                            ctx = contextlib.nullcontext()
                            is_uneven = (
                                tensor_dims_unflatten[shard_dim] % mesh.size(0) != 0
                            )
                            is_last_dim = shard_dim == flatten_end - 1
                            if is_uneven and not is_last_dim:
                                ctx = self.assertRaisesRegex(
                                    RuntimeError,
                                    "is not evenly divisible by mesh dimension",
                                )
                            with (
                                self.subTest(
                                    dims=tensor_dims_unflatten,
                                    shard=shard_dim,
                                    flat=(flatten_start, flatten_end),
                                ),
                                ctx,
                            ):
                                self._test_dtensor_unflatten_1d_shard(
                                    tensor_dims_unflatten,
                                    local_tensor_dims_unflatten,
                                    tensor_dims_flatten,
                                    flatten_start,
                                    expected_placements,
                                    mesh,
                                )

        # any factoring on unflatten_dim
        for tensor_ndim in [1, 2, 3, 4]:
            for unflatten_dim in range(tensor_ndim):
                for shard_dim in range(tensor_ndim):
                    for tensor_dims in self.generate_tensor_dims_1d_after_flatten(
                        tensor_ndim, unflatten_dim, shard_dim, mesh
                    ):
                        with self.subTest(
                            dims=tensor_dims, shard=shard_dim, unflatten=unflatten_dim
                        ):
                            placements = (Shard(shard_dim),)
                            self._test_dtensor_unflatten_1d_shard_arbitrary(
                                tensor_dims,
                                unflatten_dim,
                                placements,
                                mesh,
                            )

        # Replicate: unflatten should preserve Replicate placement
        for tensor_ndim in [1, 2, 3, 4]:
            for unflatten_dim in range(tensor_ndim):
                tensor_dims = [6] * tensor_ndim
                tensor_dims[unflatten_dim] = 12  # will unflatten to (3, 4)
                global_tensor = torch.arange(math.prod(tensor_dims)).view(tensor_dims)
                dt = distribute_tensor(
                    global_tensor, mesh, (Replicate(),), src_data_rank=None
                )
                # Unflatten dimension to (3, 4)
                unflatten_shape = list(tensor_dims)
                unflatten_shape[unflatten_dim : unflatten_dim + 1] = [3, 4]
                dt_unflattened = dt.view(unflatten_shape)
                self.assertEqual(dt_unflattened.placements, (Replicate(),))
                self.assertEqual(dt_unflattened.shape, torch.Size(unflatten_shape))