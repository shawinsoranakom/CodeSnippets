def test_dtensor_flatten_multi_mesh(self):
        """Test flatten operations across 1D and 2D meshes with all placement patterns.

        Iterates over 1D and 2D mesh configurations to test single-shard (S, SR, RS),
        multi-shard (SS), and replicate (R, RR) patterns with even/uneven tensor dim sizes.
        """
        cases = [
            ((6,), [("S",), ("R",)]),
            ((3, 2), [("S", "R"), ("R", "S"), ("S", "S"), ("R", "R")]),
        ]
        for mesh_shape, patterns in cases:
            if self.world_size < math.prod(mesh_shape):
                continue
            mesh = init_device_mesh(self.device_type, mesh_shape)
            mesh_ndim = len(mesh_shape)
            for pattern in patterns:
                shard_mesh_dims = [i for i, p in enumerate(pattern) if p == "S"]
                num_shard = len(shard_mesh_dims)
                for tensor_ndim in [2, 3, 4]:
                    for flatten_start in range(tensor_ndim):
                        for flatten_end in range(flatten_start + 2, tensor_ndim + 1):
                            if num_shard == 1:
                                self._run_flatten_single_shard(
                                    mesh,
                                    mesh_ndim,
                                    shard_mesh_dims[0],
                                    tensor_ndim,
                                    flatten_start,
                                    flatten_end,
                                )
                            elif num_shard == 2:
                                self._run_flatten_ss(
                                    mesh,
                                    tensor_ndim,
                                    flatten_start,
                                    flatten_end,
                                )
                            else:
                                even = 2 * mesh.size(0)
                                dim_vals = [even - 1, even, even + 1]
                                all_dims = list(
                                    itertools.product(dim_vals, repeat=tensor_ndim)
                                )
                                rep_placements = tuple([Replicate()] * mesh_ndim)
                                for tensor_dims in all_dims:
                                    with self.subTest(
                                        dims=tensor_dims,
                                        flat=(flatten_start, flatten_end),
                                        mesh=mesh_shape,
                                    ):
                                        self._test_dtensor_flatten_replicate(
                                            tensor_dims,
                                            flatten_start,
                                            flatten_end,
                                            mesh,
                                            rep_placements,
                                        )