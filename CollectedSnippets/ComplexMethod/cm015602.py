def test_multi_dim_redistribute(self):
        """Test various redistribute patterns for correctness and comm count optimization.

        Each test case is: (mesh_shape, flattened_dims, src_placements, dst_placements, expected_comm_counts)
        - mesh_shape: tuple of mesh dimensions
        - flattened_dims: list of tuples of dims to flatten, e.g., [("A", "B")] or None
        - src_placements: source placements
        - dst_placements: target placements
        - expected_comm_counts: dict of {collective_op: count} for verification
        """
        # Pre-create meshes to avoid repeated init_device_mesh overhead
        mesh_2d = init_device_mesh(self.device_type, (4, 2), mesh_dim_names=("A", "B"))
        mesh_2d["A", "B"]._flatten("A_B")

        mesh_3d = init_device_mesh(
            self.device_type, (2, 2, 2), mesh_dim_names=("A", "B", "C")
        )
        mesh_3d["A", "B"]._flatten("A_B")
        mesh_3d["A", "C"]._flatten("A_C")
        mesh_3d["A", "B", "C"]._flatten("A_B_C")

        # Define test cases: (mesh, src_placements, dst_placements, expected_comm_counts, desc)
        test_cases = [
            # ===== 2D mesh cases =====
            (
                mesh_2d,
                (Partial("sum"), Partial("sum")),
                (Replicate(), Replicate()),
                {funcol.all_reduce: 1},
                "2 allreduces merged to 1",
            ),
            (
                mesh_2d,
                (Partial("sum"), Partial("sum")),
                (Shard(0), Shard(0)),
                {funcol.reduce_scatter_tensor: 1},
                "nested reduce_scatter",
            ),
            (
                mesh_2d,
                (Partial("sum"), Partial("sum")),
                (Shard(0), Shard(1)),
                {funcol.reduce_scatter_tensor: 2},
                "reduce_scatter to different dims",
            ),
            (
                mesh_2d,
                (Shard(0), Shard(0)),
                (Replicate(), Replicate()),
                {funcol.all_gather_into_tensor: 1},
                "2 allgathers nested",
            ),
            (
                mesh_2d,
                (Shard(0), Shard(1)),
                (Replicate(), Replicate()),
                {funcol.all_gather_into_tensor: 2},
                "2 separate allgathers",
            ),
            # ===== 3D mesh cases =====
            (
                mesh_3d,
                (Partial("sum"), Partial("sum"), Shard(0)),
                (Shard(0), Shard(0), Shard(0)),
                {
                    funcol.reduce_scatter_tensor: 1,
                    funcol.all_reduce: 1,
                    funcol.all_gather_into_tensor: 1,
                },
                "Partial,Partial,Shard -> Shard,Shard,Shard",
            ),
            (
                mesh_3d,
                (Partial("sum"), Partial("sum"), Partial("sum")),
                (Replicate(), Replicate(), Replicate()),
                {funcol.all_reduce: 1},
                "3 allreduces merged to 1",
            ),
            (
                mesh_3d,
                (Partial("sum"), Shard(0), Partial("sum")),
                (Replicate(), Replicate(), Replicate()),
                {funcol.all_reduce: 2, funcol.all_gather_into_tensor: 1},
                "non-consecutive allreduces with shard in between",
            ),
            (
                mesh_3d,
                (Partial("sum"), Replicate(), Partial("sum")),
                (Replicate(), Replicate(), Replicate()),
                {funcol.all_reduce: 1},
                "non-consecutive allreduces with replica in between",
            ),
            (
                mesh_3d,
                (Partial("sum"), Partial("sum"), Replicate()),
                (Shard(0), Shard(1), Replicate()),
                {funcol.reduce_scatter_tensor: 2},
                "reduce_scatter with Replicate unchanged",
            ),
            (
                mesh_3d,
                (Partial("sum"), Partial("sum"), Partial("sum")),
                (Shard(0), Shard(0), Shard(1)),
                {funcol.reduce_scatter_tensor: 2},
                "3 partials: 2 merged reduce_scatter + 1 separate",
            ),
        ]

        for mesh, src_placements, dst_placements, expected_counts, desc in test_cases:
            with self.subTest(desc=desc):
                # Create global tensor - size must be divisible by mesh for sharding
                global_shape = tuple(16 for _ in range(max(3, mesh.ndim)))
                global_tensor = torch.randn(global_shape, device=self.device_type)

                # Create source DTensor
                # For Partial dims, use Replicate then reinterpret as Partial
                src_for_distribute = [
                    Replicate() if p.is_partial() else p for p in src_placements
                ]
                base_dt = distribute_tensor(
                    global_tensor, mesh, list(src_for_distribute)
                )
                local = base_dt.to_local()
                dt = DTensor.from_local(local, mesh, src_placements, run_check=False)

                # Redistribute with comm tracking
                comm_mode = CommDebugMode()
                with comm_mode:
                    result = dt.redistribute(mesh, list(dst_placements))

                # Check comm counts
                for op, expected_count in expected_counts.items():
                    actual_count = comm_mode.get_comm_counts().get(op, 0)
                    self.assertEqual(
                        actual_count,
                        expected_count,
                        f"{desc}: expected {expected_count} {op}, got {actual_count}",
                    )

                # Verify placements
                self.assertEqual(tuple(result.placements), tuple(dst_placements))

                # Verify numerical correctness via full_tensor
                # The full tensor should equal global_tensor * (product of partial mesh dim sizes)
                num_partial_sums = 1
                for i, p in enumerate(src_placements):
                    if p.is_partial():
                        num_partial_sums *= mesh.size(i)

                result_full = result.full_tensor()
                expected_full = global_tensor * num_partial_sums
                self.assertEqual(result_full, expected_full)