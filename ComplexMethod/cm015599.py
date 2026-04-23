def test_redistribute_shard_dim_change(self, dtype):
        # test 1d device mesh
        mesh_1d = self.build_device_mesh()
        data_to_test = [
            # evenly sharded case
            torch.randn((8, 8), device=self.device_type, dtype=dtype),
            # 3d or more dims
            torch.randn((8, 8, 8), device=self.device_type, dtype=dtype),
            # uneven case 1
            torch.randn((8, 5), device=self.device_type, dtype=dtype),
            # uneven case 2
            torch.randn((5, 8), device=self.device_type, dtype=dtype),
            # uneven case 3
            torch.randn((5, 5), device=self.device_type, dtype=dtype),
        ]

        sharding_src_dst_pairs = [([Shard(0)], [Shard(1)]), ([Shard(1)], [Shard(0)])]

        comm_mode = CommDebugMode()

        for input_data in data_to_test:
            for src, dst in sharding_src_dst_pairs:
                expected_dt = distribute_tensor(input_data.clone(), mesh_1d, dst)
                sharded_dt = distribute_tensor(input_data, mesh_1d, src)
                with comm_mode:
                    out_dt = sharded_dt.redistribute(mesh_1d, dst)
                self.assertEqual(out_dt.placements, expected_dt.placements)
                local_out_dt = out_dt.to_local()
                local_expected_dt = expected_dt.to_local()
                self.assertEqual(out_dt.to_local(), expected_dt.to_local())
                if torch.accelerator.is_available():
                    self.assertEqual(
                        comm_mode.get_comm_counts()[
                            torch.ops._dtensor.shard_dim_alltoall
                        ],
                        1,
                    )
                else:
                    # TODO: Integrate local tensor with CommDebugMode
                    if not self.is_local_tensor_enabled:
                        self.assertEqual(
                            comm_mode.get_comm_counts()[funcol.all_gather_into_tensor],
                            1,
                        )

        # test 2d device mesh
        mesh_2d = DeviceMesh(
            self.device_type, torch.arange(self.world_size).reshape(2, 2)
        )
        data_to_test_2d = [
            # evenly sharded case
            torch.randn((8, 8), device=self.device_type, dtype=dtype),
            # 3d or more dims
            torch.randn((8, 8, 8), device=self.device_type, dtype=dtype),
            # uneven case 1
            torch.randn((8, 5), device=self.device_type, dtype=dtype),
            # uneven case 2
            torch.randn((5, 8), device=self.device_type, dtype=dtype),
            # uneven case 3
            torch.randn((5, 5), device=self.device_type, dtype=dtype),
        ]
        sharding_src_dst_pairs_2d = [
            ([Shard(0), Shard(1)], [Shard(0), Shard(0)]),
            ([Shard(0), Shard(1)], [Shard(1), Shard(0)]),
            ([Shard(0), Shard(0)], [Shard(1), Shard(1)]),
        ]
        comm_counts_2d = [
            1,  # 1: S1 -> S0
            2,  # 1: S1 -> R, 0: S0 -> S1, 1: R -> S0
            2,  # 1: S0 -> R, 0: S0 -> S1, 1: R -> S1
        ]

        for input_data in data_to_test_2d:
            if input_data.ndim > 2:
                sharding_spec_combs = sharding_src_dst_pairs_2d + [
                    ([Shard(0), Shard(2)], [Shard(1), Shard(0)]),
                    ([Shard(1), Shard(1)], [Shard(1), Shard(2)]),
                ]
                comm_counts_2d = comm_counts_2d + [
                    2,  # 1. S2 -> R, 0: S0 -> S1, 1: R -> S0
                    1,  # 1: S1 -> S2
                ]
            else:
                sharding_spec_combs = sharding_src_dst_pairs_2d

            for idx, (src, dst) in enumerate(sharding_spec_combs):
                expected_dt = distribute_tensor(input_data.clone(), mesh_2d, dst)
                sharded_dt = distribute_tensor(input_data, mesh_2d, src)
                with comm_mode:
                    out_dt = sharded_dt.redistribute(mesh_2d, dst)

                self.assertEqual(out_dt.placements, expected_dt.placements)
                if not self.is_local_tensor_enabled:
                    self.assertEqual(comm_mode.get_total_counts(), comm_counts_2d[idx])

                local_out_dt = out_dt.to_local()
                local_expected_dt = expected_dt.to_local()
                self.assertEqual(local_out_dt, local_expected_dt)