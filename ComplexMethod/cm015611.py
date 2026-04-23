def test_dtensor_flatten_unflatten_2d_reversed_mesh(self):
        """Test flatten/unflatten with reversed mesh shape (2, 3) to catch ordering bugs."""
        self.assertEqual(self.world_size, 6)
        mesh = init_device_mesh(self.device_type, (2, self.world_size // 2))
        dim_size = mesh.size(0) * mesh.size(1) * 2  # divisible by both mesh dims

        # Flatten with (S, S) pattern
        tensor_ndim = 3
        for flatten_start in range(tensor_ndim):
            for flatten_end in range(flatten_start + 2, tensor_ndim + 1):
                for shard_dim0 in range(flatten_start, flatten_end):
                    for shard_dim1 in range(shard_dim0, flatten_end):
                        with self.subTest(
                            shard0=shard_dim0,
                            shard1=shard_dim1,
                            flat=(flatten_start, flatten_end),
                        ):
                            tensor_dims = tuple([dim_size] * tensor_ndim)
                            placements = (Shard(shard_dim0), Shard(shard_dim1))
                            self._test_dtensor_flatten_2d_ss(
                                tensor_dims,
                                flatten_start,
                                flatten_end,
                                mesh,
                                placements,
                            )

        # Unflatten with (SS, SS) pattern — representative factorizations
        factors_list = [(6, 4, 3), (4, 6, 2), (3, 2, 6), (2, 6, 4)]
        for factors in factors_list:
            for shard_idx0 in range(1, len(factors) - 1):
                for shard_idx1 in range(shard_idx0 + 1, len(factors)):
                    with self.subTest(factors=factors, s0=shard_idx0, s1=shard_idx1):
                        factor0 = factors[shard_idx0]
                        factor1 = factors[shard_idx1]
                        uneven0 = factor0 % mesh.size(0) != 0
                        is_last1 = shard_idx1 == len(factors) - 1
                        uneven1 = factor1 % mesh.size(1) != 0 and not is_last1
                        if uneven0 or uneven1:
                            with self.assertRaisesRegex(
                                RuntimeError, "is not evenly divisible"
                            ):
                                self._test_dtensor_unflatten_factors(
                                    factors,
                                    (shard_idx0, shard_idx1),
                                    0,
                                    mesh,
                                )
                        else:
                            self._test_dtensor_unflatten_factors(
                                factors,
                                (shard_idx0, shard_idx1),
                                0,
                                mesh,
                            )