def test_triton_minmax_reduce(self, dtype) -> None:
        torch.manual_seed(42 + self.rank)
        self._init_device()
        group_name = dist.distributed_c10d._get_default_group().group_name
        world_size = dist.get_world_size()
        rank = self.rank
        # Configuration
        nreduce = 2  # number of values to reduce
        # Source buffers for min and max
        src_min = symm_mem.empty(nreduce, dtype=dtype, device=self.device)
        src_max = symm_mem.empty(nreduce, dtype=dtype, device=self.device)
        # Each rank contributes different values
        # For min: rank 0: [10, 20], rank 1: [15, 5], etc.
        # For max: same values
        for i in range(nreduce):
            if i == 0:
                src_min[i] = 10 + rank * 5  # 10, 15, 20, ...
                src_max[i] = 10 + rank * 5
            else:
                src_min[i] = 20 - rank * 15  # 20, 5, -10, ...
                src_max[i] = 20 - rank * 15
        # Destination buffers
        dst_min = symm_mem.empty(nreduce, dtype=dtype, device=self.device).fill_(-1)
        dst_max = symm_mem.empty(nreduce, dtype=dtype, device=self.device).fill_(-1)
        symm_mem.rendezvous(src_min, group=group_name)
        symm_mem.rendezvous(src_max, group=group_name)
        symm_mem.rendezvous(dst_min, group=group_name)
        symm_mem.rendezvous(dst_max, group=group_name)
        # Calculate expected results
        all_values = []
        for i in range(nreduce):
            values = []
            for r in range(world_size):
                if i == 0:
                    values.append(10 + r * 5)
                else:
                    values.append(20 - r * 15)
            all_values.append(values)
        expected_min = [min(vals) for vals in all_values]
        expected_max = [max(vals) for vals in all_values]
        dist.barrier()
        # Execute MIN reduction
        team_handle = 0
        my_reduce_kernel[(1,)](
            team_handle,
            dst_min,
            src_min,
            nreduce,
            operation="min",
            launch_cooperative_grid=True,
        )
        # Execute MAX reduction
        my_reduce_kernel[(1,)](
            team_handle,
            dst_max,
            src_max,
            nreduce,
            operation="max",
            launch_cooperative_grid=True,
        )
        dist.barrier()
        # Verify results
        torch.testing.assert_close(
            dst_min, torch.tensor(expected_min, device=self.device, dtype=dtype)
        )
        torch.testing.assert_close(
            dst_max, torch.tensor(expected_max, device=self.device, dtype=dtype)
        )