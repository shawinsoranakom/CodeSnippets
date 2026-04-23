def test_dtensor_unflatten_multi_mesh(self):
        """Test unflatten across 2D and 3D meshes with all placement patterns.

        Iterates over 2D and 3D mesh configurations to test multi-shard (SS, SSS),
        mixed (R+SS, RR+SS), and replicate (RR, RRR) patterns.
        """
        # (mesh_shape, num_replicate_dims)
        cases = [
            ((3, 2), 0),  # (SS, SS)
            ((3, 2), 1),  # (R, SS)
            ((3, 2), 2),  # (R, R)
            ((2, 2, 2), 0),  # (SS, SS, SS)
            ((2, 2, 2), 1),  # (R, SS, SS)
            ((2, 2, 2), 2),  # (R, R, SS)
            ((2, 2, 2), 3),  # (R, R, R)
        ]
        for mesh_shape, num_rep in cases:
            if self.world_size < math.prod(mesh_shape):
                continue
            mesh = init_device_mesh(self.device_type, mesh_shape)
            mesh_ndim = len(mesh_shape)
            num_shard = mesh_ndim - num_rep
            flattened_size = math.prod(mesh_shape) * 12
            factorizations = self._get_all_factorizations(flattened_size)

            if num_shard == 0:
                # All-replicate: test that Replicate is preserved
                for factors in factorizations:
                    for prefix_size in [0, 1, 2]:
                        with self.subTest(
                            factors=factors,
                            prefix=prefix_size,
                            mesh=mesh_shape,
                        ):
                            tensor_dims_unflatten = (
                                [6] * prefix_size + list(factors) + [3]
                            )
                            nelem_flatten = math.prod(factors)
                            tensor_dims_flatten = (
                                [6] * prefix_size + [nelem_flatten] + [3]
                            )
                            nelem = math.prod(tensor_dims_flatten)
                            global_tensor = torch.arange(nelem).view(
                                tensor_dims_flatten
                            )
                            rep_placements = tuple([Replicate()] * mesh_ndim)
                            dt = distribute_tensor(
                                global_tensor,
                                mesh,
                                rep_placements,
                                src_data_rank=None,
                            )
                            dt_unflattened = dt.view(tensor_dims_unflatten)
                            self.assertEqual(
                                dt_unflattened.placements,
                                rep_placements,
                            )
                            self.assertEqual(
                                dt_unflattened.shape,
                                torch.Size(tensor_dims_unflatten),
                            )
            else:
                # Sharded cases: pick shard indices from factorizations
                min_factors = num_shard + 1  # need prefix + num_shard shard dims
                valid = [f for f in factorizations if len(f) >= min_factors]
                for factors in valid:
                    n = len(factors)
                    for shard_indices in itertools.combinations(
                        range(1, n),
                        num_shard,
                    ):
                        # Error detection: uneven on non-(last-shard AND last-factor)
                        expect_error = False
                        for rank, si in enumerate(shard_indices):
                            mesh_dim = num_rep + rank
                            is_last_shard = rank == num_shard - 1
                            is_last_factor = si == n - 1
                            if factors[si] % mesh.size(mesh_dim) != 0 and not (
                                is_last_shard and is_last_factor
                            ):
                                expect_error = True
                                break
                        with self.subTest(
                            factors=factors,
                            shard=shard_indices,
                            mesh=mesh_shape,
                        ):
                            if expect_error:
                                with self.assertRaisesRegex(
                                    RuntimeError,
                                    "is not evenly divisible by mesh dimension|"
                                    "do not support inputs with use_strided_shard_as_shard_order",
                                ):
                                    self._test_dtensor_unflatten_factors(
                                        factors,
                                        shard_indices,
                                        num_rep,
                                        mesh,
                                    )
                            else:
                                self._test_dtensor_unflatten_factors(
                                    factors,
                                    shard_indices,
                                    num_rep,
                                    mesh,
                                )