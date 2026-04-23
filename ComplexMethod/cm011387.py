def __new__(
        cls, local_shards: list[torch.Tensor], local_offsets: list[tuple[int, ...]]
    ) -> "LocalShardsWrapper":
        if not all(
            tensor.device == local_shards[0].device for tensor in local_shards[1:]
        ):
            raise AssertionError

        # if empty shard, we create a empty tensor
        if len(local_shards) == 0:
            r = torch.Tensor._make_wrapper_subclass(
                cls,
                torch.Size([0, 0]),
            )
            r._local_shards = []
            r._storage_meta = TensorStorageMetadata(
                properties=TensorProperties(),
                size=torch.Size([0, 0]),
                chunks=[
                    ChunkStorageMetadata(
                        offsets=torch.Size([0, 0]), sizes=torch.Size([0, 0])
                    )
                ],
            )
            return r

        # we calculate the total tensor size by "concat" on second tensor dimension
        cat_tensor_shape = list(local_shards[0].size())
        if len(local_shards) > 1 and local_shards[0].ndim == 2:  # column-wise sharding
            for shard in local_shards[1:]:
                cat_tensor_shape[1] += shard.size()[1]

        # in cases of sharding optimizer rowwise, we calculate total tensor size by "concat" on first tensor dimension
        if len(local_shards) > 1 and local_shards[0].ndim == 1:  # column-wise sharding
            for shard in local_shards[1:]:
                cat_tensor_shape[0] += shard.size()[0]

        wrapper_properties = TensorProperties.create_from_tensor(local_shards[0])
        wrapper_shape = torch.Size(cat_tensor_shape)
        chunks_meta = [
            ChunkStorageMetadata(
                offsets=torch.Size(offset),
                sizes=shard.size(),
            )
            for shard, offset in zip(local_shards, local_offsets)
        ]

        r = torch.Tensor._make_wrapper_subclass(
            cls,
            torch.Size(cat_tensor_shape),
        )
        r._local_shards = local_shards
        r._storage_meta = TensorStorageMetadata(
            properties=wrapper_properties,
            size=wrapper_shape,
            chunks=chunks_meta,
        )

        return r