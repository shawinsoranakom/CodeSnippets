def test_dtensor_flatten_shard_outside_range(self):
        """Test that Shard on a dim outside the flatten range passes through correctly.

        When flattening dims [flatten_start, flatten_end), a Shard on a dim outside
        this range should be preserved with adjusted dim index:
        - Shard before range: dim unchanged
        - Shard after range: dim shifts by -(flatten_end - flatten_start - 1)
        """
        mesh = init_device_mesh(self.device_type, (self.world_size,))
        # Use sizes divisible by mesh size to avoid uneven-shard complications
        dim_size = mesh.size(0) * 2
        test_cases = [
            # (tensor_dims, flatten_start, flatten_end, shard_dim, expected_shard_dim)
            # Shard before range
            ([dim_size] * 3, 1, 3, 0, 0),
            ([dim_size] * 4, 1, 3, 0, 0),
            ([dim_size] * 4, 2, 4, 0, 0),
            ([dim_size] * 4, 2, 4, 1, 1),
            # Shard after range
            ([dim_size] * 4, 0, 2, 2, 1),
            ([dim_size] * 4, 0, 2, 3, 2),
            ([dim_size] * 4, 0, 3, 3, 1),
            ([dim_size] * 4, 1, 3, 3, 2),
        ]

        for (
            tensor_dims,
            flatten_start,
            flatten_end,
            shard_dim,
            expected_shard_dim,
        ) in test_cases:
            with self.subTest(
                dims=tensor_dims, shard=shard_dim, flat=(flatten_start, flatten_end)
            ):
                placements = (Shard(shard_dim),)
                nelem = math.prod(tensor_dims)
                global_inps = torch.arange(nelem).view(tensor_dims)
                dt = distribute_tensor(
                    global_inps, mesh, placements, src_data_rank=None
                )

                flat_dims = self._get_viewed_tensor_dims(
                    tensor_dims, flatten_start, flatten_end
                )
                comm_mode = CommDebugMode()
                with comm_mode:
                    dt_flat = dt.view(flat_dims)

                expected_placements = (Shard(expected_shard_dim),)
                self.assertEqual(dt_flat.placements, expected_placements)
                expected_local = distribute_tensor(
                    global_inps.view(flat_dims),
                    mesh,
                    expected_placements,
                    src_data_rank=None,
                )._local_tensor
                self.assertEqual(dt_flat._local_tensor, expected_local)
                self.assertEqual(comm_mode.get_total_counts(), 0)

        # 2D mesh: test shard outside range with (Shard, Replicate) and (Replicate, Shard)
        mesh_2d = init_device_mesh(self.device_type, (3, self.world_size // 3))
        dim_size_2d = mesh_2d.size(0) * mesh_2d.size(1) * 2
        test_cases_2d = [
            # (tensor_dims, flatten_start, flatten_end, shard_dim)
            ([dim_size_2d] * 4, 0, 2, 2),  # shard after range
            ([dim_size_2d] * 4, 0, 2, 3),  # shard after range
            ([dim_size_2d] * 4, 1, 3, 0),  # shard before range
            ([dim_size_2d] * 4, 2, 4, 0),  # shard before range
            ([dim_size_2d] * 4, 2, 4, 1),  # shard right before range
        ]
        for tensor_dims, flatten_start, flatten_end, shard_dim in test_cases_2d:
            num_merged = flatten_end - flatten_start - 1
            expected_shard_dim = (
                shard_dim if shard_dim < flatten_start else shard_dim - num_merged
            )
            for mesh_dim_idx in range(2):
                with self.subTest(
                    dims=tensor_dims, shard=shard_dim, mesh_dim=mesh_dim_idx
                ):
                    placements = tuple(
                        Shard(shard_dim) if i == mesh_dim_idx else Replicate()
                        for i in range(2)
                    )
                    nelem = math.prod(tensor_dims)
                    global_inps = torch.arange(nelem).view(tensor_dims)
                    dt = distribute_tensor(
                        global_inps, mesh_2d, placements, src_data_rank=None
                    )

                    flat_dims = self._get_viewed_tensor_dims(
                        tensor_dims, flatten_start, flatten_end
                    )
                    comm_mode = CommDebugMode()
                    with comm_mode:
                        dt_flat = dt.view(flat_dims)

                    expected_placements = tuple(
                        Shard(expected_shard_dim) if i == mesh_dim_idx else Replicate()
                        for i in range(2)
                    )
                    self.assertEqual(dt_flat.placements, expected_placements)
                    expected_local = distribute_tensor(
                        global_inps.view(flat_dims),
                        mesh_2d,
                        expected_placements,
                        src_data_rank=None,
                    )._local_tensor
                    self.assertEqual(dt_flat._local_tensor, expected_local)
                    self.assertEqual(comm_mode.get_total_counts(), 0)