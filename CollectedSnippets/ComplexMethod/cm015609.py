def _test_dtensor_unflatten_1d_shard_arbitrary(
        self, tensor_dims, unflatten_dim, placements, mesh
    ):
        shard_dim = placements[0].dim
        self.assertIsInstance(placements[0], Shard)
        self.assertNotIsInstance(placements[0], _StridedShard)

        tensor_dims = list(tensor_dims)  # Make a mutable copy

        # Get all non-trivial factorizations of unflatten_dim size
        unflatten_size = tensor_dims[unflatten_dim]
        factorizations = self._get_all_factorizations(unflatten_size)

        # Skip if no non-trivial factorization exists (prime number)
        if not factorizations:
            return

        # Create the global tensor once (reused for all factorizations)
        nelem = math.prod(tensor_dims)
        global_inps = torch.arange(nelem).view(tensor_dims)

        # Distribute the tensor
        inps = distribute_tensor(global_inps, mesh, placements, src_data_rank=None)

        # Test each factorization (can be any length >= 2)
        for factors in factorizations:
            tensor_dims_unflatten = (
                tensor_dims[:unflatten_dim]
                + list(factors)
                + tensor_dims[unflatten_dim + 1 :]
            )

            # Determine if we expect an error
            first_factor = factors[0]

            ctx = contextlib.nullcontext()
            expect_error = False

            if shard_dim == unflatten_dim:
                # When unflattening the sharded dimension, check factor alignment
                uneven_shard = tensor_dims[shard_dim] % mesh.size(0) != 0
                first_factor_aligned = first_factor % mesh.size(0) == 0

                expect_error = not first_factor_aligned or uneven_shard

            if expect_error:
                ctx = self.assertRaisesRegex(
                    RuntimeError, "is not evenly divisible by mesh dimension"
                )

            with ctx:
                comm_mode = CommDebugMode()
                with comm_mode:
                    inps_viewed = inps.view(tensor_dims_unflatten)

                # Number of new dimensions added by unflatten
                num_new_dims = len(factors) - 1

                # Compute expected placements after unflatten
                if shard_dim < unflatten_dim:
                    expected_placements = (Shard(shard_dim),)
                elif shard_dim == unflatten_dim:
                    expected_placements = (Shard(unflatten_dim),)
                else:
                    expected_placements = (Shard(shard_dim + num_new_dims),)

                self.assertEqual(inps_viewed.placements, expected_placements)
                self.assertEqual(comm_mode.get_total_counts(), 0)

                expected_local = distribute_tensor(
                    global_inps.view(tensor_dims_unflatten),
                    mesh,
                    expected_placements,
                    src_data_rank=None,
                )._local_tensor
                self.assertEqual(inps_viewed._local_tensor, expected_local)