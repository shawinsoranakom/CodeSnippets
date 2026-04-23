def test_reduce_scatter_offset_uneven(self, dim: int):
        """reduce_scatter_offset with uneven block sizes: j=0 and j=1 own blocks
        of different sizes, verifying that out[j] shapes differ across j."""
        symm_mem.set_backend("NCCL")
        torch.cuda.set_device(self.rank)
        c10d.all_reduce(torch.ones(1, device=self.device))
        group_name = c10d.group.WORLD.group_name

        rows, cols = 64, 32
        # j=0 blocks have size_0 along dim; j=1 blocks have size_1 along dim.
        # Arrange blocks as [size_0] * world_size + [size_1] * world_size so
        # that round-robin assigns each rank exactly one block of each size.
        size_0, size_1 = 16, 48
        block_sizes = [size_0] * self.world_size + [size_1] * self.world_size
        offsets = []
        total = 0
        for sz in block_sizes:
            total += sz
            offsets.append(total)

        n_experts = 2 * self.world_size
        if dim == 1:
            buf = symm_mem.empty(rows, total, dtype=torch.float, device=self.device)
            pos = 0
            for i, sz in enumerate(block_sizes):
                buf[:, pos : pos + sz] = float((self.rank + 1) * (i + 1))
                pos += sz
        else:
            buf = symm_mem.empty(total, cols, dtype=torch.float, device=self.device)
            pos = 0
            for i, sz in enumerate(block_sizes):
                buf[pos : pos + sz, :] = float((self.rank + 1) * (i + 1))
                pos += sz
        symm_mem.rendezvous(buf, group=group_name)

        dst_ranks = [i % self.world_size for i in range(n_experts)]
        if dim == 1:
            out = [
                torch.zeros(rows, size_0, dtype=torch.float, device=self.device),
                torch.zeros(rows, size_1, dtype=torch.float, device=self.device),
            ]
        else:
            out = [
                torch.zeros(size_0, cols, dtype=torch.float, device=self.device),
                torch.zeros(size_1, cols, dtype=torch.float, device=self.device),
            ]

        symm_mem.reduce_scatter_offset(
            buf, out, group_name, dim=dim, offsets=offsets, dst_ranks=dst_ranks
        )
        torch.cuda.synchronize()

        rank_sum = float(sum(r + 1 for r in range(self.world_size)))
        for j in range(2):
            expert_idx = self.rank + j * self.world_size
            expected = float(expert_idx + 1) * rank_sum
            self.assertEqual(
                out[j],
                torch.full_like(out[j], expected),
                msg=f"rank {self.rank}: out[{j}] should contain the reduced sum",
            )