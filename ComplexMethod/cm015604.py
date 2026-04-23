def test_dtensor_flatten_split_multi_mesh(self):
        """Test views producing Split(Flatten) rules.

        Complements test_dtensor_flatten_multi_mesh (pure Flatten rules) and
        test_dtensor_unflatten_multi_mesh (pure Split(InputDim) rules) by
        covering the hybrid case: an input dim crosses two output groups,
        so view_groups produces Split(Flatten(...)) rules.

        Uses {2*M-1, 2*M, 2*M+1} dim values (M = mesh size for the shard
        mesh dim) to cover even/uneven divisibility, following the same
        pattern as _run_flatten_single_shard.
        """
        for mesh_shape in [(self.world_size,), (3, 2)]:
            if self.world_size < math.prod(mesh_shape):
                continue
            mesh = init_device_mesh(self.device_type, mesh_shape)
            for shard_mesh_dim in range(mesh.ndim):
                M = mesh.size(shard_mesh_dim)
                dim_vals = [2 * M - 1, 2 * M, 2 * M + 1]
                for a, b in itertools.product(dim_vals, repeat=2):
                    in_shape = (a, b)
                    total = a * b
                    all_factors = self._get_all_factorizations(total)
                    for out_shape in all_factors:
                        if in_shape == out_shape:
                            continue
                        rules = view_groups(list(in_shape), list(out_shape))
                        if not any(
                            isinstance(r, Split) and isinstance(r.input_dim, Flatten)
                            for r in rules
                        ):
                            continue
                        for shard_dim in range(len(in_shape)):
                            if in_shape[shard_dim] % M != 0:
                                continue
                            placements = tuple(
                                Shard(shard_dim) if i == shard_mesh_dim else Replicate()
                                for i in range(mesh.ndim)
                            )
                            with self.subTest(
                                in_shape=in_shape,
                                out_shape=out_shape,
                                shard=shard_dim,
                                mesh_dim=shard_mesh_dim,
                                mesh_shape=mesh_shape,
                            ):
                                self._test_dtensor_flatten_split_case(
                                    in_shape,
                                    out_shape,
                                    placements,
                                    mesh,
                                )