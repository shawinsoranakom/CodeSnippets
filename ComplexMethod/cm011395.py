def _split_tensor(
        self,
        tensor: torch.Tensor,
        num_chunks: int,
        *,
        with_padding: bool = True,
        contiguous: bool = True,
    ) -> tuple[list[torch.Tensor], list[int]]:
        if self.dim > tensor.ndim:
            raise AssertionError(
                f"Sharding dim {self.dim} greater than tensor ndim {tensor.ndim}"
            )

        # Essentially _StridedShard express the right-to-left sharding in the
        # reversed order. Here we perform first_split as the virtual "right" sharding,
        # and then second_split as the virtual "left" sharding, and finally assemble
        # results in the transposed left-first order.

        # First split: chunk into split_factor pieces
        first_split = list(torch.chunk(tensor, self.split_factor, dim=self.dim))
        first_split = fill_empty_tensor_to_shards(
            first_split, self.dim, self.split_factor - len(first_split)
        )

        # Second split: chunk each piece into num_chunks pieces
        second_split = []
        for s in first_split:
            chunks = list(torch.chunk(s, num_chunks, dim=self.dim))
            chunks = fill_empty_tensor_to_shards(
                chunks, self.dim, num_chunks - len(chunks)
            )
            second_split.append(chunks)

        shard_list: list[torch.Tensor] = []
        for i in range(num_chunks):
            shard = torch.cat(
                [second_split[j][i] for j in range(self.split_factor)],
                dim=self.dim,
            )
            if contiguous:
                shard = shard.contiguous()
            shard_list.append(shard)

        # The amount of padding is determined by the local chunk with the largest size.
        pad_sizes: list[int] = []
        max_chunk_size = max([shard.size(self.dim) for shard in shard_list])
        if with_padding:
            pad_sizes = [max_chunk_size - shard.size(self.dim) for shard in shard_list]

        return shard_list, pad_sizes