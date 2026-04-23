def __get_tensor_shard__(self, index: MetadataIndex) -> torch.Tensor:
        """
        For compatibility with DCP, we support finding shard based on index
        Return a 'torch.Tensor' shard based on 'MetadataIndex'.
        """
        # Fast lookup path
        if index.index is not None:
            if (
                len(self._local_shards) > index.index
                and self._storage_meta.chunks[index.index].offsets == index.offset
            ):
                return self._local_shards[index.index]

        if index.offset is not None:
            for shard, chunk in zip(self._local_shards, self._storage_meta.chunks):
                if chunk.offsets == index.offset:
                    return shard

        # Empty shard case
        if len(self._local_shards) == 0 and self._storage_meta.chunks[
            0
        ].sizes == torch.Size([0, 0]):
            return torch.empty(0)

        raise ValueError(
            f"Could not find shard at '{index.offset}' for FQN: '{index.fqn}'"
        )