def _init_sharded_param(
        self,
        param: nn.Parameter,
        device: torch.device,
        shard_placement_fn: Callable[[nn.Parameter], ShardPlacementFnResult] | None,
        mesh_info: DataParallelMeshInfo,
    ):
        if callable(shard_placement_fn):
            shard_result = resolve_shard_placement(
                shard_placement_fn(param),
                cast(FSDPMeshInfo, mesh_info),
            )
            self.mesh_info = shard_result.mesh_info
            fsdp_placement = shard_result.placement
        else:
            self.mesh_info = mesh_info  # pyrefly: ignore[bad-assignment]
            fsdp_placement = None
        self._shard_mesh = self._init_shard_mesh()
        if param.device != device and param.device.type != "meta":
            raise AssertionError(
                f"Expects the parameter to already be moved to device {device} but got {param.device}"
            )
        if not param.is_contiguous():
            raise NotImplementedError(
                f"FSDP does not support non-contiguous parameters yet: {param.shape=} {param.stride()=}"
            )
        if fsdp_placement is None:
            fsdp_placement = Shard(0)
        elif fsdp_placement.dim < 0:
            fsdp_placement = Shard(fsdp_placement.dim + param.ndim)
        if not isinstance(fsdp_placement, Shard):
            raise AssertionError(
                f"Expected Shard, got {type(fsdp_placement)}: {fsdp_placement}"
            )
        self.fsdp_placement = fsdp_placement
        shard_dim = fsdp_placement.dim
        # TODO: Replace the sharded DTensor parameter construction logic with
        # `distribute_tensor` after https://github.com/pytorch/pytorch/issues/116101
        # TODO: Simplify the following sharded parameter padding logic after
        # https://github.com/pytorch/pytorch/issues/113045
        self.is_dtensor = isinstance(param, DTensor)
        self._orig_param_uid = _get_orig_param_uid(param)
        param_data = self._init_sharding_spec(param, fsdp_placement, shard_dim)
        if not param_data.is_contiguous():
            raise AssertionError(
                f"Expected contiguous tensor, got {param_data.shape=} {param_data.stride()=}"
            )
        shard_dim = fsdp_placement.dim
        if shard_dim >= param_data.ndim:
            raise AssertionError(
                f"Shard dim {shard_dim} is invalid for {param_data.ndim}D tensor: {param.shape}"
            )
        self._orig_size = param_data.size()
        self._contiguous_orig_stride = make_contiguous_strides_for(self._orig_size)
        if isinstance(self.mesh_info, FSDPMeshInfo):  # FSDP or HSDP
            shard_rank = self.mesh_info.shard_mesh_rank
            shard_world_size = self.mesh_info.shard_mesh_size
        else:  # DDP
            shard_rank = 0
            shard_world_size = 1

        if shard_dim > 0 and param_data.size(shard_dim) % shard_world_size != 0:
            # If sharding on nonzero dim, require even sharding for now because
            # the uneven sharding (1) requires extra copies before/after FSDP
            # collectives and (2) introduces extra complexity to handle padding
            # and unpadding
            raise NotImplementedError(
                f"FSDP does not support uneven sharding on dim {shard_dim}: "
                f"{param_data.size()} (world size: {shard_world_size})"
            )
        chunks = _chunk_with_empty(param_data, shard_world_size, dim=shard_dim)
        sharded_param = chunks[shard_rank]
        self.sharded_size = _get_dim_chunked_size(
            sharded_param, param_data.size(), dim=shard_dim
        )
        self.contiguous_sharded_stride = make_contiguous_strides_for(self.sharded_size)
        padded_sharded_size = chunks[0].size()  # 0th always padded
        self.padded_sharded_param_size = padded_sharded_size
        # Pre-pad the sharded parameter to avoid padding before all-gather
        padded_sharded_param = param_data.new_zeros(padded_sharded_size)
        if sharded_param.numel() > 0:
            padded_sharded_param.narrow(
                dim=shard_dim, start=0, length=sharded_param.size(shard_dim)
            ).copy_(sharded_param)
        if self.offload_to_cpu and not padded_sharded_param.is_meta:
            padded_sharded_param = padded_sharded_param.cpu()
            if self.pin_memory:
                padded_sharded_param = padded_sharded_param.pin_memory()
        self._sharded_param_data = padded_sharded_param.view(-1)
        length = sharded_param.size(shard_dim) if sharded_param.numel() > 0 else 0
        sharded_param = padded_sharded_param.narrow(
            dim=shard_dim, start=0, length=length
        )
        if not sharded_param.is_contiguous():
            raise AssertionError(
                f"Expected contiguous tensor with {self.fsdp_placement=}"
            )
        self.sharded_param = nn.Parameter(
            self.to_sharded_dtensor(sharded_param),
            requires_grad=param.requires_grad,
        )
        # Let `param_data` be freed normally when its ref count reaches 0 when
        # the `fully_shard` call returns to allow provided parameters to alias
        self._setattr_on_modules(self.sharded_param)
        self.sharded_state = ShardedState.SHARDED