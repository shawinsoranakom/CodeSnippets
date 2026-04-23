def test_batch_send_recv_subgroup(self, group_rank):
        world_size = 4
        if self.rank >= world_size:
            return
        subgroup = self._init_two_pg2_subgroups(world_size)
        device = torch.device(f"cuda:{self.rank:d}")
        ops = []
        if self.rank == 0 or self.rank == 2:
            x = torch.empty((10,), device=device)
            if group_rank:
                ops.append(c10d.P2POp(dist.irecv, x, group=subgroup, group_peer=1))
            else:
                ops.append(
                    c10d.P2POp(dist.irecv, x, peer=self.rank + 1, group=subgroup)
                )

            for work in dist.batch_isend_irecv(ops):
                work.wait()
            expected = torch.ones((10,), device=device) * (self.rank + 1)
            self.assertEqual(x, expected)
        else:
            x = torch.ones((10,), device=device) * self.rank
            if group_rank:
                ops.append(c10d.P2POp(dist.isend, x, group=subgroup, group_peer=0))
            else:
                ops.append(
                    c10d.P2POp(dist.isend, x, peer=self.rank - 1, group=subgroup)
                )
            for work in dist.batch_isend_irecv(ops):
                work.wait()