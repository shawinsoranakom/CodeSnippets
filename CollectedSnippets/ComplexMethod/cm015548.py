def test_new_group(self):
        spec = EnumerableShardingSpec(
            [
                ShardMetadata(
                    shard_offsets=[0, 0],
                    shard_sizes=[5, 5],
                    placement="rank:1/cuda:1",
                ),
                ShardMetadata(
                    shard_offsets=[5, 0],
                    shard_sizes=[5, 5],
                    placement="rank:3/cuda:3",
                ),
            ]
        )

        pg = dist.new_group(ranks=[1, 2, 3])

        st = sharded_tensor.empty(spec, 10, 5, process_group=pg, init_rrefs=True)
        self.assertEqual((10, 5), st.size())
        if self.rank == 1 or self.rank == 3:
            # Verify local shard.
            local_shard = st.local_shards()[0]
            self.assertEqual(
                torch.device(f"cuda:{self.rank}"), local_shard.tensor.device
            )
            self.assertEqual((5, 5), local_shard.tensor.size())

            # Verify local shard metadata.
            self.assertEqual(
                (self.rank // 2 * 5, 0), local_shard.metadata.shard_offsets
            )
            self.assertEqual((5, 5), local_shard.metadata.shard_sizes)
            self.assertEqual(
                f"rank:{self.rank}/cuda:{self.rank}",
                str(local_shard.metadata.placement),
            )

        # Verify global metadata.
        st_metadata = st.metadata()
        shards_metadata = st_metadata.shards_metadata
        self.assertEqual(2, len(shards_metadata))
        for rank, shard_metadata in enumerate(shards_metadata):
            self.assertEqual((rank * 5, 0), shard_metadata.shard_offsets)
            self.assertEqual((5, 5), shard_metadata.shard_sizes)
            self.assertEqual(
                f"rank:{rank * 2 + 1}/cuda:{rank * 2 + 1}",
                str(shard_metadata.placement),
            )

        # Validate remote shards.
        remote_shards = st.remote_shards()
        if self.rank == 1 or self.rank == 3:
            self.assertEqual(1, len(remote_shards))
        else:
            self.assertEqual(2, len(remote_shards))

        for rpc_rank, shards in remote_shards.items():
            self.assertEqual(1, len(shards))

            for remote_shard in shards:
                self.assertEqual(rpc_rank, remote_shard.owner().id)
                shard = remote_shard.to_here()
                self.assertEqual((5, 5), shard.tensor.size())