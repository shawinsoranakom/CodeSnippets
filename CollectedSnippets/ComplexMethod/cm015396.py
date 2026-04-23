def test_gather_subgroup(self, group_rank):
        world_size = 4
        if self.rank >= world_size:
            # just easier to write the test for exactly 4 gpus, even if this test class increased to 8gpu later
            return

        subgroup = self._init_two_pg2_subgroups(world_size)
        device = torch.device(f"cuda:{self.rank:d}")
        input = torch.ones((10,), device=device) * self.rank
        if self.rank == 0 or self.rank == 2:
            gather_list = [torch.empty_like(input) for _ in range(subgroup.size())]
            if group_rank:
                # global_dst=0 group_dst=0 my_global_rank=2 gather_list is not None=True
                torch.distributed.gather(
                    input,
                    gather_list=gather_list,
                    group_dst=0,
                    group=subgroup,
                    async_op=False,
                )
            else:
                torch.distributed.gather(
                    input,
                    gather_list=gather_list,
                    dst=self.rank,
                    group=subgroup,
                    async_op=False,
                )
            for src in range(len(gather_list)):
                expected = (torch.ones_like(input) * self.rank) + src
                self.assertEqual(gather_list[src], expected)
        else:
            if group_rank:
                torch.distributed.gather(
                    input,
                    gather_list=None,
                    group_dst=0,
                    group=subgroup,
                    async_op=False,
                )
            else:
                torch.distributed.gather(
                    input,
                    gather_list=None,
                    dst=self.rank - 1,
                    group=subgroup,
                    async_op=False,
                )