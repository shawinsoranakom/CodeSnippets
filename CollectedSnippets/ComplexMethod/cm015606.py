def _run_flatten_ss(self, mesh, tensor_ndim, flatten_start, flatten_end):
        for shard_dim0 in range(flatten_start, flatten_end):
            for shard_dim1 in range(shard_dim0, flatten_end):
                dim0_values = [
                    2 * mesh.size(0) - 1,
                    2 * mesh.size(0),
                    2 * mesh.size(0) + 1,
                ]
                dim1_values = [
                    2 * mesh.size(1) - 1,
                    2 * mesh.size(1),
                    2 * mesh.size(1) + 1,
                ]
                other_dim_value = 2 * mesh.size(0) * mesh.size(1)
                for dim0_val in dim0_values:
                    for dim1_val in dim1_values:
                        tensor_dims = [other_dim_value] * tensor_ndim
                        tensor_dims[shard_dim0] = dim0_val
                        if shard_dim0 != shard_dim1:
                            tensor_dims[shard_dim1] = dim1_val
                        tensor_dims = tuple(tensor_dims)
                        local_tensor_dims = list(tensor_dims)
                        placements = (Shard(shard_dim0), Shard(shard_dim1))
                        ctx = contextlib.nullcontext()
                        if local_tensor_dims[shard_dim0] % mesh.size(0) != 0:
                            ctx = self.assertRaisesRegex(
                                RuntimeError,
                                "is not evenly divisible by mesh dimension",
                            )
                        local_tensor_dims[shard_dim0] = local_tensor_dims[
                            shard_dim0
                        ] // mesh.size(0)
                        if local_tensor_dims[shard_dim1] % mesh.size(
                            1
                        ) != 0 and shard_dim1 != (flatten_end - 1):
                            ctx = self.assertRaisesRegex(
                                RuntimeError,
                                "is not evenly divisible by mesh dimension",
                            )
                        with (
                            self.subTest(
                                dims=tensor_dims,
                                shard0=shard_dim0,
                                shard1=shard_dim1,
                            ),
                            ctx,
                        ):
                            self._test_dtensor_flatten_2d_ss(
                                tensor_dims,
                                flatten_start,
                                flatten_end,
                                mesh,
                                placements,
                            )