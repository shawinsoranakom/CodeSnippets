def check_shard_sampler(self, dataset, batch_size, drop_last, num_processes=2):
        shards = [
            ShardSampler(
                dataset, batch_size=batch_size, drop_last=drop_last, num_processes=num_processes, process_index=i
            )
            for i in range(num_processes)
        ]
        shard_lists = [list(shard) for shard in shards]

        for shard in shard_lists:
            # All shards have a number of samples that is a round multiple of batch size
            self.assertTrue(len(shard) % batch_size == 0)
            # All shards have the same number of samples
            self.assertEqual(len(shard), len(shard_lists[0]))

        observed = []
        for idx in range(0, len(shard_lists[0]), batch_size):
            for shard in shard_lists:
                observed += shard[idx : idx + batch_size]

        # If drop_last is False we loop through samples at the beginning to have a size that is a round multiple of
        # batch_size
        reference = copy.copy(dataset)
        if not drop_last:
            while len(reference) < len(observed):
                reference += reference
        self.assertListEqual(observed, reference[: len(observed)])