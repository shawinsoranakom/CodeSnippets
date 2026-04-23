def gather(  # type: ignore[override]
        self,
        dst: int = 0,
        out: torch.Tensor | None = None,
        enforce_dtype: bool = False,
        dtype: torch.dtype | None = None,
    ) -> None:
        """
        Creates a full :class:`Tensor` on rank ``dst`` by gathering all shards of the
        sharded tensor.

        The API needs to be called on all ranks in SPMD fashion. All ranks should have
        the same ``dst``. ``out`` should be a tensor of the same size as the overall
        size of the sharded tensor on ``dst`` and ``None`` on all other ranks.

        Args:
            dst(int): The rank where full tensor is constructed.
                Default: 0
            out (:class `torch.Tensor`, optional): The output full tensor.
                Must to be provided ONLY on ``dst`` rank.
                Default: ``None``
            enforce_dtype (bool): Deprecated, please use dtype instead.  Force the
                gathered tensors to be the same type as input and output.
            dtype (torch.dtype): Force the gathered tensors to be this dtype.
                Default: ``None``
        """

        def shard_size(shard_md):
            return reduce(operator.mul, shard_md.shard_sizes)  # type: ignore[attr-defined]

        if enforce_dtype:
            warnings.warn(
                "`enforce_dtype` is deprecated. Please use `dtype` instead.",
                FutureWarning,
                stacklevel=2,
            )

        rank = dist.get_rank(self._process_group)
        full_size = self.metadata().size
        _validate_output_tensor_for_gather(rank, dst, full_size, out)

        local_shards = self.local_shards()
        world_size = dist.get_world_size(self._process_group)
        rank_sizes = [0 for _ in range(world_size)]
        max_rank_size = 0
        shard_placement: dict[ShardMetadata, tuple[int, int]] = {}
        # collect sizes
        for shard_md in self.metadata().shards_metadata:
            shard_rank = cast(_remote_device, shard_md.placement).rank()
            if shard_rank is None:
                raise AssertionError

            shard_placement[shard_md] = (shard_rank, rank_sizes[shard_rank])
            rank_sizes[shard_rank] += shard_size(shard_md)
            max_rank_size = max(max_rank_size, rank_sizes[shard_rank])

        gather_list: list[torch.Tensor] | None
        if rank == dst:
            if out is None:
                raise AssertionError
            if enforce_dtype:
                # enforce_dtype is deprecated.  Do it for backward compatibility.
                dtype = out.dtype
            # TODO make it as a view of out tensor
            gather_list = [
                torch.empty((max_rank_size,), device=out.device, dtype=dtype)
                for _ in range(world_size)
            ]
        else:
            gather_list = None

        with torch.no_grad():
            if enforce_dtype and len(local_shards) > 0:
                # enforce_dtype is deprecated.  Do it for backward compatibility.
                dtype = local_shards[0].tensor.dtype
            data = torch.empty(
                max_rank_size, device=self._get_preferred_device(), dtype=dtype
            )

            for shard in local_shards:
                src = shard.tensor.flatten()
                if src.nelement() == 0:
                    warnings.warn(
                        "Gathering a tensor with zero elements on rank " + str(rank),
                        stacklevel=2,
                    )
                    continue
                shard_offset = shard_placement[shard.metadata][1]
                data[shard_offset : shard_offset + src.numel()].copy_(src)

        dist.gather(
            tensor=data,
            gather_list=gather_list,
            dst=dst,
            group=self._process_group,
        )
        if rank != dst:
            return
        # In _validate_output_tensor_for_gather, we raise if out == None and rank == dst
        out = cast(torch.Tensor, out)
        if gather_list is None:
            raise AssertionError

        full_size = self.metadata().size
        dims = len(full_size)
        for shard_md in self.metadata().shards_metadata:
            rank, rank_offset = shard_placement[shard_md]
            tensor = gather_list[rank]
            tensor = tensor[rank_offset : rank_offset + shard_size(shard_md)]
            tensor = tensor.view(shard_md.shard_sizes)

            out_narrow_view = out
            for dim in range(dims):
                out_narrow_view = out_narrow_view.narrow(
                    dim,
                    shard_md.shard_offsets[dim],
                    shard_md.shard_sizes[dim],
                )

            out_narrow_view.copy_(tensor)