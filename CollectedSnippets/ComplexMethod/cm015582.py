def test_deterministic_uniform_2d(self):
        mesh = torch.arange(self.world_size).reshape(2, 2)
        device_mesh = DeviceMesh(self.device_type, mesh)
        dtensor = distribute_tensor(
            torch.empty(
                *[self.world_size for _ in mesh.size()], device=self.device_type
            ),
            device_mesh,
            [Replicate(), Replicate()],
        )

        placements_list = [  # this list of placements should be enough to cover
            [Shard(0), Shard(1)],
            [Shard(1), Shard(0)],
            [Shard(0), Replicate()],
            [Replicate(), Shard(0)],
            [Shard(1), Replicate()],
            [Replicate(), Shard(1)],
            [Replicate(), Replicate()],
        ]

        shard_index_list = [
            {0: 0, 1: 1, 2: 2, 3: 3},
            {0: 0, 1: 2, 2: 1, 3: 3},
            {0: 0, 1: 0, 2: 1, 3: 1},
            {0: 0, 1: 1, 2: 0, 3: 1},
            {0: 0, 1: 0, 2: 1, 3: 1},
            {0: 0, 1: 1, 2: 0, 3: 1},
            {0: 0, 1: 0, 2: 0, 3: 0},
        ]

        coordinate = device_mesh.get_coordinate()
        if coordinate is None:
            raise AssertionError("Expected coordinate to not be None")

        for placements, shard_index in zip(placements_list, shard_index_list):
            dtensor = dtensor.redistribute(device_mesh, placements)

            # random op call
            dtensor.uniform_(0, 1)

            # check shard information is correct
            shard_coord = [
                coordinate[mesh_dim] if mesh_dim >= 0 else 0
                for mesh_dim in dtensor._spec.dim_map
            ]

            shard_size = [
                device_mesh.size(mesh_dim) if mesh_dim >= 0 else 1
                for mesh_dim in dtensor._spec.dim_map
            ]

            shard_linear_idx = random._rng_tracker._calc_shard_linear_idx(
                shard_coord, shard_size
            )

            @maybe_run_for_local_tensor
            def check_shard_index(shard_linear_idx, rank):
                self.assertEqual(shard_linear_idx, shard_index[rank])

            check_shard_index(shard_linear_idx, self.rank)

            # compute local size and offset
            _, local_shard_offset = compute_local_shape_and_global_offset(
                dtensor.shape, device_mesh, placements
            )

            # get the local shard size and local shard offset for each shard
            # local_shard_list_on_dim[i] has the list of all shards on that dim
            # as a tuple (local_shard_offset, local_shard_size)
            dtensor_shape = dtensor.shape
            local_shard_list_on_dim: list[list[tuple[int, int]]] = [
                [(0, l)] for l in dtensor_shape
            ]
            for idx, placement in enumerate(placements):
                if isinstance(placement, Shard):
                    mesh_dim_size = device_mesh.size(idx)
                    shard_dim = placement.dim
                    local_shard_list_on_dim[shard_dim] = []
                    for shard_idx_on_dim in range(mesh_dim_size):
                        (
                            shard_size,
                            shard_offset,
                        ) = placement._local_shard_size_and_offset(
                            dtensor_shape[shard_dim],
                            mesh_dim_size,
                            shard_idx_on_dim,
                        )
                        local_shard_list_on_dim[shard_dim].append(
                            (not_none(shard_offset), shard_size)
                        )

            local_shard_comb = itertools.product(*local_shard_list_on_dim)

            # the local shard
            local_tensor = dtensor.to_local()
            # allgather the local tensors
            full_tensor = dtensor.full_tensor()

            full_tensor = (
                full_tensor.reconcile()
                if isinstance(full_tensor, LocalTensor)
                else full_tensor
            )

            @maybe_run_for_local_tensor
            def blockwise_iter_if_localtensor(local_tensor, local_shard_offset):
                # compare local tensor with each other shard
                for other_local_shard in local_shard_comb:
                    other_local_shard_offset, _ = zip(*other_local_shard)
                    slice_idx = [
                        slice(offset, offset + size)
                        for offset, size in other_local_shard
                    ]
                    if local_shard_offset == other_local_shard_offset:
                        self.assertEqual(full_tensor[tuple(slice_idx)], local_tensor)
                    else:
                        self.assertNotEqual(full_tensor[tuple(slice_idx)], local_tensor)

            blockwise_iter_if_localtensor(local_tensor, local_shard_offset)