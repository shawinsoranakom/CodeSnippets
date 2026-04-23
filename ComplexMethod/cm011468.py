def __new__(
        cls, local_shards: list[torch.Tensor], offsets: list[torch.Size]
    ) -> "LocalShardsWrapper":
        if len(local_shards) <= 0:
            raise AssertionError
        if len(local_shards) != len(offsets):
            raise AssertionError
        if local_shards[0].ndim != 2:
            raise AssertionError
        # we calculate the total tensor size by "concat" on second tensor dimension
        cat_tensor_shape = list(local_shards[0].shape)
        if len(local_shards) > 1:  # column-wise sharding
            for shard_size in [s.shape for s in local_shards[1:]]:
                cat_tensor_shape[1] += shard_size[1]

        # according to DCP, each chunk is expected to have the same properties of the
        # TensorStorageMetadata that includes it. Vice versa, the wrapper's properties
        # should also be the same with that of its first chunk.
        wrapper_properties = TensorProperties.create_from_tensor(local_shards[0])
        wrapper_shape = torch.Size(cat_tensor_shape)
        chunks_meta = [
            ChunkStorageMetadata(o, s.shape) for s, o in zip(local_shards, offsets)
        ]

        r = torch.Tensor._make_wrapper_subclass(
            cls,
            wrapper_shape,
        )
        r.shards = local_shards
        r.storage_meta = TensorStorageMetadata(
            properties=wrapper_properties,
            size=wrapper_shape,
            chunks=chunks_meta,
        )

        return r