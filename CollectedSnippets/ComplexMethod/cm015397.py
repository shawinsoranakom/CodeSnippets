def test_send_recv_subgroup(self, async_op, group_rank):
        world_size = 4
        if self.rank >= world_size:
            return
        subgroup = self._init_two_pg2_subgroups(world_size)
        device = torch.device(f"cuda:{self.rank:d}")
        if self.rank == 0 or self.rank == 2:
            x = torch.empty((10,), device=device)
            if async_op:
                if group_rank:
                    c10d.irecv(x, group_src=1, group=subgroup).wait()
                else:
                    c10d.irecv(x, src=self.rank + 1, group=subgroup).wait()
            else:
                if group_rank:
                    c10d.recv(x, group_src=1, group=subgroup)
                else:
                    c10d.recv(x, src=self.rank + 1, group=subgroup)
            expected = torch.ones((10,), device=device) * (self.rank + 1)
            self.assertEqual(x, expected)
        else:
            x = torch.ones((10,), device=device) * self.rank
            if async_op:
                if group_rank:
                    c10d.isend(x, group_dst=0, group=subgroup).wait()
                else:
                    c10d.isend(x, dst=self.rank - 1, group=subgroup).wait()
            else:
                if group_rank:
                    c10d.send(x, group_dst=0, group=subgroup)
                else:
                    c10d.send(x, dst=self.rank - 1, group=subgroup)