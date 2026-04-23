def test_compute_local_shape_and_global_offset_uneven(self):
        # This case is not only 'uneven' bug also has an empty shard
        # (e.g. most DP ranks have local shape 18,4096, one has 8,4096, one has 0,4096
        global_shape = (4096, 4096)
        DP = 30
        TP = 8
        mesh_shape = (DP, TP)
        placements = [_StridedShard(0, split_factor=8), Shard(0)]
        TP_shard_size = global_shape[0] / TP
        for my_coordinate in itertools.product(range(DP), range(TP)):
            local_shape, global_offset = _compute_local_shape_and_global_offset(
                global_shape, mesh_shape, lambda idx: my_coordinate[idx], placements
            )
            dp_rank, tp_rank = my_coordinate
            expected_shard_size = 18
            expected_shard_offset = tp_rank * TP_shard_size + 18 * dp_rank
            if dp_rank == 28:
                expected_shard_size = 8
            elif dp_rank == 29:
                expected_shard_size = 0
                # we define the offset value of a zero-sized shard as the dim size
                # this actually matters, because DCP uses offset to deduplicate shards when saving
                expected_shard_offset = 4096
            self.assertEqual(local_shape, (expected_shard_size, 4096))
            self.assertEqual(global_offset, (expected_shard_offset, 0))

        # S, S uneven without empty
        global_shape = (18, 2)
        DP = 4
        TP = 2
        mesh_shape = (DP, TP)
        placements = [Shard(0), Shard(0)]
        for my_coordinate in itertools.product(range(DP), range(TP)):
            dp_rank, tp_rank = my_coordinate
            local_shape, global_offset = _compute_local_shape_and_global_offset(
                global_shape, mesh_shape, lambda idx: my_coordinate[idx], placements
            )

            dp012_shard_size = 5
            if dp_rank in (0, 1, 2):
                tp0_shard_size = 3
                if tp_rank == 0:
                    expected_shard_offset = dp012_shard_size * dp_rank
                    expected_shard_size = 3
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = dp012_shard_size * dp_rank + tp0_shard_size
                    expected_shard_size = 2
            else:
                if dp_rank != 3:
                    raise AssertionError(f"Expected dp_rank == 3, got {dp_rank}")
                tp0_shard_size = 2
                if tp_rank == 0:
                    expected_shard_offset = dp012_shard_size * dp_rank
                    expected_shard_size = 2
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = dp012_shard_size * dp_rank + tp0_shard_size
                    expected_shard_size = 1
            self.assertEqual(local_shape, (expected_shard_size, 2))
            self.assertEqual(global_offset, (expected_shard_offset, 0))

        # S, S uneven with empty
        global_shape = (13, 2)
        DP = 4
        TP = 2
        mesh_shape = (DP, TP)
        placements = [Shard(0), Shard(0)]
        for my_coordinate in itertools.product(range(DP), range(TP)):
            dp_rank, tp_rank = my_coordinate
            local_shape, global_offset = _compute_local_shape_and_global_offset(
                global_shape, mesh_shape, lambda idx: my_coordinate[idx], placements
            )

            dp012_shard_size = 4
            if dp_rank in (0, 1, 2):
                tp0_shard_size = 2
                if tp_rank == 0:
                    expected_shard_offset = dp012_shard_size * dp_rank
                    expected_shard_size = 2
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = dp012_shard_size * dp_rank + tp0_shard_size
                    expected_shard_size = 2
            else:
                if dp_rank != 3:
                    raise AssertionError(f"Expected dp_rank == 3, got {dp_rank}")
                tp0_shard_size = 1
                if tp_rank == 0:
                    expected_shard_offset = dp012_shard_size * dp_rank
                    expected_shard_size = 1
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = global_shape[0]
                    expected_shard_size = 0
            self.assertEqual(local_shape, (expected_shard_size, 2))
            self.assertEqual(global_offset, (expected_shard_offset, 0))

        # SS, Shard
        global_shape = (18, 2)
        DP = 4
        TP = 2
        mesh_shape = (DP, TP)
        placements = [_StridedShard(0, split_factor=TP), Shard(0)]
        TP_shard_size = int(global_shape[0] / TP)
        for my_coordinate in itertools.product(range(DP), range(TP)):
            dp_rank, tp_rank = my_coordinate
            local_shape, global_offset = _compute_local_shape_and_global_offset(
                global_shape, mesh_shape, lambda idx: my_coordinate[idx], placements
            )
            expected_shard_size = 3
            expected_shard_offset = (
                tp_rank * TP_shard_size + expected_shard_size * dp_rank
            )
            if dp_rank == 3:
                expected_shard_size = 0
                expected_shard_offset = 18
            self.assertEqual(local_shape, (expected_shard_size, 2))
            self.assertEqual(global_offset, (expected_shard_offset, 0))

        # SS, SS
        global_shape = (39, 2)
        DP = 4
        TP = 2
        mesh_shape = (DP, TP)
        placements = [
            _StridedShard(0, split_factor=3),
            _StridedShard(0, split_factor=4),
        ]
        for my_coordinate in itertools.product(range(DP), range(TP)):
            dp_rank, tp_rank = my_coordinate
            local_shape, global_offset = _compute_local_shape_and_global_offset(
                global_shape, mesh_shape, lambda idx: my_coordinate[idx], placements
            )
            if dp_rank in (0, 1, 2):
                tp0_shard_size = 8
                if tp_rank == 0:
                    expected_shard_offset = 4 * dp_rank
                    expected_shard_size = tp0_shard_size
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = 4 * dp_rank + 2
                    expected_shard_size = 4
            else:
                if dp_rank != 3:
                    raise AssertionError(f"Expected dp_rank == 3, got {dp_rank}")
                tp0_shard_size = 3
                if tp_rank == 0:
                    expected_shard_offset = 4 * dp_rank
                    expected_shard_size = 3
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = global_shape[0]
                    expected_shard_size = 0
            self.assertEqual(local_shape, (expected_shard_size, 2))
            self.assertEqual(global_offset, (expected_shard_offset, 0))

        # (Shard, SS)
        global_shape = (18, 2)
        DP = 4
        TP = 2
        mesh_shape = (DP, TP)
        placements = [Shard(0), _StridedShard(0, split_factor=2)]
        for my_coordinate in itertools.product(range(DP), range(TP)):
            dp_rank, tp_rank = my_coordinate
            local_shape, global_offset = _compute_local_shape_and_global_offset(
                global_shape, mesh_shape, lambda idx: my_coordinate[idx], placements
            )
            if dp_rank in (0, 1, 2):
                tp0_shard_size = 3
                if tp_rank == 0:
                    expected_shard_offset = 5 * dp_rank
                    expected_shard_size = tp0_shard_size
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = 5 * dp_rank + 2
                    expected_shard_size = 2
            else:
                if dp_rank != 3:
                    raise AssertionError(f"Expected dp_rank == 3, got {dp_rank}")
                if tp_rank == 0:
                    expected_shard_offset = 5 * dp_rank
                    expected_shard_size = 2
                else:
                    if tp_rank != 1:
                        raise AssertionError(f"Expected tp_rank == 1, got {tp_rank}")
                    expected_shard_offset = 5 * dp_rank + 1
                    expected_shard_size = 1
            self.assertEqual(local_shape, (expected_shard_size, 2))
            self.assertEqual(global_offset, (expected_shard_offset, 0))

        # (Shard, SS, Shard)
        global_shape = (39, 2)
        mesh0, mesh1, mesh2 = 4, 2, 3
        mesh_shape = (mesh0, mesh1, mesh2)
        placements = [Shard(0), _StridedShard(0, split_factor=2), Shard(0)]
        for my_coordinate in itertools.product(
            range(mesh0), range(mesh1), range(mesh2)
        ):
            mesh0_rank, mesh1_rank, mesh2_rank = my_coordinate
            local_shape, global_offset = _compute_local_shape_and_global_offset(
                global_shape, mesh_shape, lambda idx: my_coordinate[idx], placements
            )
            if mesh0_rank in (0, 1, 2):
                if mesh1_rank == 0:
                    if mesh2_rank == 0:
                        expected_shard_offset = 10 * mesh0_rank
                        expected_shard_size = 2
                    elif mesh2_rank == 1:
                        expected_shard_offset = 10 * mesh0_rank + 2
                        expected_shard_size = 2
                    else:
                        expected_shard_offset = 10 * mesh0_rank + 6
                        expected_shard_size = 2
                else:
                    if mesh1_rank != 1:
                        raise AssertionError(
                            f"Expected mesh1_rank == 1, got {mesh1_rank}"
                        )
                    if mesh2_rank == 0:
                        expected_shard_offset = 10 * mesh0_rank + 3
                        expected_shard_size = 2
                    elif mesh2_rank == 1:
                        expected_shard_offset = 10 * mesh0_rank + 8
                        expected_shard_size = 2
                    else:
                        if mesh2_rank != 2:
                            raise AssertionError(
                                f"Expected mesh2_rank == 2, got {mesh2_rank}"
                            )
                        expected_shard_size = 0
                        expected_shard_offset = global_shape[0]
            else:
                if mesh0_rank != 3:
                    raise AssertionError(f"Expected mesh0_rank == 3, got {mesh0_rank}")
                if mesh1_rank == 0:
                    if mesh2_rank in (0, 1):
                        expected_shard_offset = 10 * mesh0_rank + 2 * mesh2_rank
                        expected_shard_size = 2
                    else:
                        if mesh2_rank != 2:
                            raise AssertionError(
                                f"Expected mesh2_rank == 2, got {mesh2_rank}"
                            )
                        expected_shard_offset = 10 * mesh0_rank + 6
                        expected_shard_size = 1
                else:
                    if mesh1_rank != 1:
                        raise AssertionError(
                            f"Expected mesh1_rank == 1, got {mesh1_rank}"
                        )
                    if mesh2_rank == 0:
                        expected_shard_offset = 10 * mesh0_rank + 3
                        expected_shard_size = 2
                    elif mesh2_rank == 1:
                        expected_shard_offset = 10 * mesh0_rank + 7
                        expected_shard_size = 2
                    else:
                        expected_shard_offset = global_shape[0]
                        expected_shard_size = 0
            self.assertEqual(local_shape, (expected_shard_size, 2))
            self.assertEqual(global_offset, (expected_shard_offset, 0))