def test_iterable_dataset_shard_with_length(self):
        sampler_shards = [
            IterableDatasetShard(list(range(100)), batch_size=4, drop_last=True, num_processes=2, process_index=i)
            for i in range(2)
        ]

        # Build expected shards: each process will have batches of size 4 until there is not enough elements to
        # form two full batches (so we stop at 96 = (100 // (4 * 2)) * 4)
        expected_shards = [[], []]
        current_shard = 0
        for i in range(0, 96, 4):
            expected_shards[current_shard].extend(list(range(i, i + 4)))
            current_shard = 1 - current_shard

        self.assertListEqual([list(shard) for shard in sampler_shards], expected_shards)
        self.assertListEqual([len(shard) for shard in sampler_shards], [len(shard) for shard in expected_shards])

        sampler_shards = [
            IterableDatasetShard(list(range(100)), batch_size=4, drop_last=False, num_processes=2, process_index=i)
            for i in range(2)
        ]
        # When drop_last=False, we get two last full batches by looping back to the beginning.
        expected_shards[0].extend(list(range(96, 100)))
        expected_shards[1].extend(list(range(0, 4)))

        self.assertListEqual([list(shard) for shard in sampler_shards], expected_shards)
        self.assertListEqual([len(shard) for shard in sampler_shards], [len(shard) for shard in expected_shards])