def test_gather_stress(self):
        pg = self.pg
        local_device_ids = self.rank_to_GPU[self.rank]
        num_gpus = len(local_device_ids)

        def gather(output_t, input_t, rootRank):
            opts = c10d.GatherOptions()
            opts.rootRank = rootRank
            if rootRank == self.rank:
                work = pg.gather(output_t, input_t, opts)
            else:
                work = pg.gather([], input_t, opts)
            work.wait()

        stress_length = 1000

        # init input
        tensors = []
        for i in range(stress_length):
            tensors.append([])
            for device_id in local_device_ids:
                tensors[i].append(torch.tensor([self.rank]).cuda(device_id))

        # init output
        output_ts = []
        for i in range(stress_length):
            output_ts.append([[] for _ in range(num_gpus)])
            for idx, ls in enumerate(output_ts[i]):
                gpu_idx = local_device_ids[idx]
                for _ in range(self.world_size):
                    ls.append(torch.tensor([-1]).cuda(gpu_idx))

        expected = [[torch.tensor([rank]) for rank in range(self.world_size)]]
        for i in range(stress_length):
            for rank in range(self.world_size):
                gather(output_ts[i], tensors[i], rank)
                # Verification
                if rank == self.rank:
                    self.assertEqual(output_ts[i], expected)