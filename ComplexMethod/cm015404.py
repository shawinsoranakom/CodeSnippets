def test_comm_recursive_split_group(self):
        store = c10d.FileStore(self.file_name, self.world_size)
        device = torch.device(f"cuda:{self.rank}")
        pg = self._create_process_group_nccl(store, self.opts(), device_id=device)
        backend = pg._get_backend(torch.device(device))

        # split the default PG into 2 subgroups, each subgroup (ng1) has 4 ranks.
        tensor1 = torch.full((1,), self.rank).cuda(device)
        ng1 = c10d.split_group(pg, [[0, 1, 2, 3], [4, 5, 6, 7]])
        backend1 = ng1._get_backend(torch.device(device))
        if self.rank < 4:
            dist.broadcast(tensor1, 0, group=ng1)
            self.assertEqual(tensor1, torch.full((1,), 0))
        else:
            dist.broadcast(tensor1, 4, group=ng1)
            self.assertEqual(tensor1, torch.full((1,), 4))

        # comm split happens eagerly since device_id is passed to init_process_group.
        self.assertEqual(backend.comm_split_count(), 1)
        self.assertEqual(backend1.comm_split_count(), 0)

        # further split ng1 into 2 subgroups, each subgroup (ng2) has 2 ranks.
        tensor2 = torch.full((1,), self.rank).cuda(device)
        ng2 = c10d.split_group(ng1, [[0, 1], [2, 3]])
        backend2 = ng2._get_backend(torch.device(device))
        self.assertEqual(backend.comm_split_count(), 1)
        self.assertEqual(backend1.comm_split_count(), 1)
        self.assertEqual(backend2.comm_split_count(), 0)

        # execute collective calls within each 2-rank pg
        if self.rank == 0 or self.rank == 1:
            dist.broadcast(tensor2, 1, group=ng2)
            self.assertEqual(tensor2, torch.full((1,), 1))

        if self.rank == 2 or self.rank == 3:
            dist.broadcast(tensor2, 2, group=ng2)
            self.assertEqual(tensor2, torch.full((1,), 2))

        if self.rank == 4 or self.rank == 5:
            dist.broadcast(tensor2, 5, group=ng2)
            self.assertEqual(tensor2, torch.full((1,), 5))

        if self.rank == 6 or self.rank == 7:
            dist.broadcast(tensor2, 6, group=ng2)
            self.assertEqual(tensor2, torch.full((1,), 6))

        # Test the case when the split changes the pg option of split group
        # while the parent pg option is not changed.
        new_pg = c10d.new_group([0, 1, 2, 3, 4, 5, 6, 7], device_id=device)
        backend_new_pg = new_pg._get_backend(torch.device(device))
        self.assertEqual(len(backend_new_pg.options.global_ranks_in_group), 8)
        c10d.split_group(new_pg, [[0, 2, 4, 6], [1, 3, 5, 7]])
        self.assertEqual(len(backend_new_pg.options.global_ranks_in_group), 8)
        # a barrier and a cuda sync before destroying all pgs.
        dist.barrier(pg)
        torch.cuda.synchronize()
        dist.destroy_process_group()