def test_init_from_local_shards_and_global_metadata_with_local_view(self):
        # testing cases where we create ST with local view, meaning we initialize other rank's metadata with 0s
        shard_offsets = [0, 1]  # valid, invalid
        for shard_offset in shard_offsets:
            local_shard_metadata = ShardMetadata(
                shard_offsets=[shard_offset, 0],
                shard_sizes=[5, 5],
                placement=f"rank:{self.rank}/cuda:{self.rank}",
            )

            shards_metadata = []
            for r in range(self.world_size):
                if r == self.rank:
                    shards_metadata.append(local_shard_metadata)
                else:
                    shards_metadata.append(
                        ShardMetadata(
                            shard_offsets=[0 if r < self.rank else 5, 0],
                            shard_sizes=[0, 0],
                            placement=f"rank:{r}/cuda:{r}",
                        )
                    )

            local_shards = [
                sharded_tensor.Shard(
                    torch.randn(5, 5, device=f"cuda:{self.rank}"), local_shard_metadata
                )
            ]

            tensor_properties = TensorProperties(
                dtype=torch.get_default_dtype(),
                layout=torch.strided,
                requires_grad=False,
                memory_format=torch.contiguous_format,
                pin_memory=False,
            )

            sharded_tensor_metadata = sharded_tensor.ShardedTensorMetadata(
                shards_metadata=shards_metadata,
                size=torch.Size([5, 5]),
                tensor_properties=tensor_properties,
            )
            if shard_offset == 0:
                # valid case
                st = ShardedTensor._init_from_local_shards_and_global_metadata(
                    local_shards,
                    sharded_tensor_metadata,
                )
            else:
                # invalid case
                with self.assertRaises(ValueError):
                    ShardedTensor._init_from_local_shards_and_global_metadata(
                        local_shards,
                        sharded_tensor_metadata,
                    )
                return

            self.assertEqual((5, 5), st.size())
            self.assertEqual(1, len(st.local_shards()))

            # Verify local shard.
            local_shard = st.local_shards()[0]
            self.assertEqual(
                torch.device(f"cuda:{self.rank}"), local_shard.tensor.device
            )
            self.assertEqual((5, 5), local_shard.tensor.size())

            # Verify local shard metadata.
            self.assertEqual(
                (0, 0),
                local_shard.metadata.shard_offsets,
            )
            self.assertEqual((5, 5), local_shard.metadata.shard_sizes)
            self.assertEqual(
                f"rank:{self.rank}/cuda:{self.rank}",
                str(local_shard.metadata.placement),
            )

            # Verify global metadata.
            shards_metadata = st.metadata().shards_metadata
            self.assertEqual(4, len(shards_metadata))
            for rank, shard_metadata in enumerate(shards_metadata):
                self.assertEqual(
                    (0 if rank <= self.rank else 5, 0), shard_metadata.shard_offsets
                )
                if rank == self.rank:
                    self.assertEqual((5, 5), shard_metadata.shard_sizes)
                else:
                    self.assertEqual((0, 0), shard_metadata.shard_sizes)
                self.assertEqual(
                    f"rank:{rank}/cuda:{rank}", str(shard_metadata.placement)
                )