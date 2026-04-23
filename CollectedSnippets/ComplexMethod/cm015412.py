def test_reduce_scatter_offset(self, experts_per_rank: int, dim: int):
        """reduce_scatter_offset: each expert gradient is reduced to its
        destination rank and written to a separate contiguous tensor; the source
        Grouped GEMM buffer is left unmodified."""
        symm_mem.set_backend("NCCL")
        torch.cuda.set_device(self.rank)
        c10d.all_reduce(torch.ones(1, device=self.device))
        group_name = c10d.group.WORLD.group_name

        rows, cols = 64, 32
        n_experts = experts_per_rank * self.world_size

        # dim=1: experts laid out as column blocks [rows, n_experts * cols]
        # dim=0: experts laid out as row blocks    [n_experts * rows, cols]
        if dim == 1:
            buf = symm_mem.empty(
                rows, n_experts * cols, dtype=torch.float, device=self.device
            )
            for i in range(n_experts):
                buf[:, i * cols : (i + 1) * cols] = float((self.rank + 1) * (i + 1))
        else:
            buf = symm_mem.empty(
                n_experts * rows, cols, dtype=torch.float, device=self.device
            )
            for i in range(n_experts):
                buf[i * rows : (i + 1) * rows, :] = float((self.rank + 1) * (i + 1))
        symm_mem.rendezvous(buf, group=group_name)

        # Round-robin: expert i is reduced to rank i % world_size.
        dst_ranks = [i % self.world_size for i in range(n_experts)]
        n_owned = sum(r == self.rank for r in dst_ranks)
        out = [
            torch.zeros(rows, cols, dtype=torch.float, device=self.device)
            for _ in range(n_owned)
        ]
        block_size = cols if dim == 1 else rows
        offsets = [i * block_size for i in range(1, n_experts + 1)]

        symm_mem.reduce_scatter_offset(
            buf, out, group_name, dim=dim, offsets=offsets, dst_ranks=dst_ranks
        )
        torch.cuda.synchronize()

        # out[j] corresponds to expert (rank + j * world_size); expected value is
        # (expert_idx + 1) * sum(r + 1 for r in range(world_size)).
        rank_sum = float(sum(r + 1 for r in range(self.world_size)))
        for j in range(n_owned):
            expert_idx = self.rank + j * self.world_size
            expected = float(expert_idx + 1) * rank_sum
            self.assertEqual(
                out[j],
                torch.full_like(out[j], expected),
                msg=f"rank {self.rank}: out[{j}] should contain the reduced sum",
            )
        # Source buffer must be unmodified.
        for i in range(n_experts):
            if dim == 1:
                src_slice = buf[:, i * cols : (i + 1) * cols]
            else:
                src_slice = buf[i * rows : (i + 1) * rows, :]
            self.assertEqual(
                src_slice,
                torch.full(
                    (rows, cols),
                    float((self.rank + 1) * (i + 1)),
                    dtype=torch.float,
                    device=self.device,
                ),
                msg=f"rank {self.rank}: source buffer block {i} should be unchanged",
            )