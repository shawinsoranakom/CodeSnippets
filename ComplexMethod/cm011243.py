def shard(
        self, tensor: torch.Tensor, src_rank: int = 0, process_group=None
    ) -> "ShardedTensor":
        """
        Args:
            src_rank: group rank relative to ``process_group``

            N.B. If ``process_group`` is None, ``src_rank`` is a global rank.
        """
        # relative imports to avoid circular dependency
        from torch.distributed._shard.sharded_tensor import ShardedTensor

        tensor_properties = sharded_tensor_meta.TensorProperties(
            dtype=tensor.dtype,
            layout=tensor.layout,
            requires_grad=tensor.requires_grad,
            memory_format=torch.contiguous_format,
            pin_memory=tensor.is_pinned(),
        )
        current_rank = dist.get_rank(process_group)
        current_global_rank = dist.get_rank()
        tensor_meta = self.build_metadata(tensor.size(), tensor_properties)
        local_shards = []
        local_tensor = None
        local_metadata = None

        tensors_to_scatter = cast(
            list[torch.Tensor | None],
            [None] * dist.get_world_size(process_group),
        )

        sharding_dim_size = tensor.size()[self.dim]  # type: ignore[index]
        chunks = len(self.placements)
        split_size = get_split_size(sharding_dim_size, chunks)
        scatter_shape = list(tensor.size())
        scatter_shape[self.dim] = split_size  # type: ignore[index]

        for shard_meta in tensor_meta.shards_metadata:
            remote_global_rank, device = _parse_and_validate_remote_device(
                process_group, shard_meta.placement
            )
            if current_rank == src_rank:
                # Reshape to get shard for this rank and we don't want autograd
                # recording here for the narrow op and 'local_shard' should be a
                # leaf variable in the autograd graph.
                narrowed_tensor = narrow_tensor(tensor, shard_meta)
                if shard_meta.shard_sizes[self.dim] < split_size:  # type: ignore[index]
                    # for the last shard that might be smaller to other shards
                    # resize the narrowed tensor to the same size and use it for
                    # the scatter collective as dist.scatter requires same size
                    # inputs on every rank
                    tensor_to_scatter = (
                        narrowed_tensor.detach().clone().resize_(scatter_shape)
                    )
                else:
                    tensor_to_scatter = narrowed_tensor.detach().clone(
                        memory_format=torch.contiguous_format
                    )

                tensors_to_scatter[
                    # pyrefly: ignore [bad-argument-type]
                    dist.get_group_rank(process_group, remote_global_rank)
                ] = tensor_to_scatter

            if current_global_rank == remote_global_rank:
                local_tensor = torch.empty(
                    scatter_shape,
                    dtype=tensor.dtype,
                    layout=tensor.layout,
                    device=device,
                )
                local_metadata = shard_meta

        # each rank should have local_tensor and local_metadata initialized if we build
        # the metadata list in a correct way.
        if local_tensor is None:
            raise AssertionError
        if local_metadata is None:
            raise AssertionError

        # Scatter the shards to all ranks in the pg
        # scatter takes the global rank as ``src``
        src_for_scatter = src_rank
        if (
            process_group is not None
            and process_group is not distributed_c10d._get_default_group()
        ):
            src_for_scatter = distributed_c10d.get_global_rank(
                process_group, src_for_scatter
            )

        tensors_to_scatter_: list[torch.Tensor] | None = None
        if current_rank == src_rank:
            tensors_to_scatter_ = []
            for t in tensors_to_scatter:
                if not isinstance(t, torch.Tensor):
                    raise AssertionError
                tensors_to_scatter_.append(t)

        dist.scatter(
            local_tensor,
            scatter_list=tensors_to_scatter_,
            src=src_for_scatter,
            group=process_group,
        )

        if list(local_tensor.size()) != local_metadata.shard_sizes:
            # detach again after receiving to ensure local shards remain a leaf node
            local_tensor = local_tensor.resize_(local_metadata.shard_sizes).detach()

        # Sync requires_grad to local_shard.
        local_tensor.requires_grad = tensor.requires_grad

        local_shards.append(Shard(tensor=local_tensor, metadata=local_metadata))

        st = ShardedTensor._init_from_local_shards_and_global_metadata(
            local_shards, tensor_meta, process_group=process_group
        )

        # Manually set sharding_spec
        st._sharding_spec = self

        return st