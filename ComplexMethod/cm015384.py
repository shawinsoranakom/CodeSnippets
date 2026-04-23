def test_scatter_stress(self):
        pg = self.pg
        local_device_ids = self.rank_to_GPU[self.rank]
        num_gpus = len(local_device_ids)

        def scatter(output_t, input_t, rootRank):
            opts = c10d.ScatterOptions()
            opts.rootRank = rootRank
            if rootRank == self.rank:
                work = pg.scatter(output_t, input_t, opts)
            else:
                work = pg.scatter(output_t, [], opts)
            work.wait()

        stress_length = 1000

        # init output
        tensors = []
        for i in range(stress_length):
            tensors.append([])
            for device_id in local_device_ids:
                tensors[i].append(torch.tensor([-1]).cuda(device_id))

        # init input
        scatter_list = []
        for i in range(stress_length):
            scatter_list.append([[] for _ in range(num_gpus)])
            for idx, ls in enumerate(scatter_list[i]):
                gpu_idx = local_device_ids[idx]
                for rank in range(self.world_size):
                    ls.append(torch.tensor([rank]).cuda(gpu_idx))

        # test each rank to scatter
        expected = [torch.tensor([self.rank])]
        for i in range(stress_length):
            for rank in range(self.world_size):
                scatter(tensors[i], scatter_list[i], rank)
                # Verification
                self.assertEqual(tensors[i], expected)