def merge_shards(self, shard_1: KinesisShard, shard_2: KinesisShard) -> None:
        if shard_1.hash_range_end + 1 != shard_2.hash_range_start:
            raise ValueError("shards are not adjacent")
        n_expected_shards_after_split = len(self.list_shards_and_statuses()) + 1

        self.kinesis.merge_shards(
            StreamName=self.stream_name,
            ShardToMerge=shard_1.shard_id,
            AdjacentShardToMerge=shard_2.shard_id,
        )

        for _ in range(100):
            shards = self.list_shards_and_statuses()
            shard_count_as_expected = len(shards) == n_expected_shards_after_split
            shard_1_status_is_updated = False
            shard_2_status_is_updated = False
            for new_shard in shards:
                if new_shard.shard_id == shard_1.shard_id and not new_shard.is_open:
                    shard_1_status_is_updated = True
                if new_shard.shard_id == shard_2.shard_id and not new_shard.is_open:
                    shard_2_status_is_updated = True
            if (
                shard_1_status_is_updated
                and shard_2_status_is_updated
                and shard_count_as_expected
            ):
                return
            time.sleep(1.0)

        raise RuntimeError("failed to wait for the target shards state after merge")