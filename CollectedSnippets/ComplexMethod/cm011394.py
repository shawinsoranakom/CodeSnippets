def _select_split_tensor(
        self,
        tensor: torch.Tensor,
        num_chunks: int,
        index: RankType,
        *,
        with_padding: bool = True,
        contiguous: bool = True,
        clone: bool = True,
    ) -> torch.Tensor:
        """
        Like _split_tensor() but only returns a single shard at the given index.

        This function splits a tensor into num_chunks shards along the Shard placement
        dimension and returns only the shard at the specified index.

        Keyword args:
            with_padding (bool, optional): when True, we pad the tensor on the last
                few ranks before calling the collectives (i.e. scatter/all_gather, etc.).
                This is because collectives usually require equal size tensor inputs.
            contiguous (bool, optional): when True, the returned shard is made contiguous.
            clone (bool, optional): when True, the returned shard is cloned.
        """
        # We don't handle SymInt with_padding yet (because that requires extra
        # work based on the shard)
        if isinstance(index, int) or with_padding:
            shards, _ = self._split_tensor(
                tensor, num_chunks, with_padding=with_padding, contiguous=False
            )
            result = shards[index]
            if clone:
                result = result.clone()
            elif contiguous:
                result = result.contiguous()
            return result

        # For the SymInt implementation just compute the value for the tensor we
        # want rather than computing all of them.

        if self.dim > tensor.ndim:
            raise AssertionError(
                f"Sharding dim {self.dim} greater than tensor ndim {tensor.ndim}"
            )

        # chunk tensor over dimension `dim` into n slices
        dim_size = tensor.size(self.dim)
        split_size = (dim_size + num_chunks - 1) // num_chunks
        # each split is split_size except (maybe) the last one...
        last_split = dim_size - split_size * (num_chunks - 1)

        start = split_size * index
        length = torch.sym_ite(index == num_chunks - 1, last_split, split_size)
        result = torch.narrow(tensor, self.dim, start, length)
        if clone:
            result = result.clone()
        elif contiguous:
            result = result.contiguous()
        return result