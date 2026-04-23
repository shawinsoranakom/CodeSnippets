def check_iterable_dataset_shard(self, dataset, batch_size, drop_last, num_processes=2, epoch=0):
        # Set the seed for the base dataset to get the proper reference.
        dataset.generator.manual_seed(epoch)
        reference = list(dataset)

        shards = [
            IterableDatasetShard(
                dataset, batch_size=batch_size, drop_last=drop_last, num_processes=num_processes, process_index=i
            )
            for i in range(num_processes)
        ]
        for shard in shards:
            shard.set_epoch(epoch)
        shard_lists = [list(shard) for shard in shards]

        for shard in shard_lists:
            # All shards have a number of samples that is a round multiple of batch size
            self.assertTrue(len(shard) % batch_size == 0)
            # All shards have the same number of samples
            self.assertEqual(len(shard), len(shard_lists[0]))

        for shard in shards:
            # All shards know the total number of samples
            self.assertEqual(shard.num_examples, len(reference))

        observed = []
        for idx in range(0, len(shard_lists[0]), batch_size):
            for shard in shard_lists:
                observed += shard[idx : idx + batch_size]

        # If drop_last is False we loop through samples at the beginning to have a size that is a round multiple of
        # batch_size
        if not drop_last:
            while len(reference) < len(observed):
                reference += reference
        self.assertListEqual(observed, reference[: len(observed)])

        # Check equivalence between IterableDataset and ShardSampler
        dataset.generator.manual_seed(epoch)
        reference = list(dataset)

        sampler_shards = [
            ShardSampler(
                reference, batch_size=batch_size, drop_last=drop_last, num_processes=num_processes, process_index=i
            )
            for i in range(num_processes)
        ]
        for shard, sampler_shard in zip(shard_lists, sampler_shards):
            self.assertListEqual(shard, list(sampler_shard))