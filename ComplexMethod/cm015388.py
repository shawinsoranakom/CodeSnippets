def test_triton_prod_reduce(self, dtype) -> None:
        torch.manual_seed(42 + self.rank)
        self._init_device()
        group_name = dist.distributed_c10d._get_default_group().group_name
        world_size = dist.get_world_size()
        rank = self.rank
        # Configuration
        nreduce = 3  # number of separate reductions
        # Source buffer - each rank contributes different values
        # Use very small values to avoid overflow, especially for small integer types
        src = symm_mem.empty(nreduce, dtype=dtype, device=self.device)
        for i in range(nreduce):
            # Use values that won't overflow even for int8: all values 1 or 2
            if i == 0:
                # For first element: rank 0,2,4... gets 1, rank 1,3,5... gets 2
                src[i] = 1 if rank % 2 == 0 else 2
            elif i == 1:
                # For second element: all get 1 (no multiplication effect)
                src[i] = 1
            else:
                # For third element: rank 0,1 get 1, rank 2,3 get 2, etc. (groups of 2)
                src[i] = 1 if (rank // 2) % 2 == 0 else 2
        # Destination buffer
        dst = symm_mem.empty(nreduce, dtype=dtype, device=self.device).fill_(-1)
        symm_mem.rendezvous(src, group=group_name)
        symm_mem.rendezvous(dst, group=group_name)
        # Calculate expected results
        vals = torch.empty(nreduce, world_size, dtype=dtype)
        vals[0, ::2] = 1
        vals[0, 1::2] = 2
        vals[1] = 1
        for rank in range(world_size):
            vals[2, rank] = 1 if (rank // 2) % 2 == 0 else 2
        expected = vals.prod(-1).tolist()

        # Synchronize before reduction
        dist.barrier()

        # Execute product reduction across all ranks
        team_handle = 0  # NVSHMEM_TEAM_WORLD
        my_reduce_kernel[(1,)](
            team_handle,
            dst,
            src,
            nreduce,
            operation="prod",
            launch_cooperative_grid=True,
        )

        # Synchronize after reduction
        dist.barrier()

        # Verify results
        torch.testing.assert_close(
            dst, torch.tensor(expected, device=self.device, dtype=dtype)
        )