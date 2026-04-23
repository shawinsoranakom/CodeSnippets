def _init_sharding_spec_tp(
        self,
        param: nn.Parameter,
        fsdp_placement: Shard,
        shard_dim: int,
    ) -> torch.Tensor:
        """TP/EP path: param is a DTensor, DP mesh is separate from TP mesh."""
        self._unsharded_dtensor_spec = cast(DTensor, param)._spec
        dp_mesh, tp_mesh = (self.mesh_info.mesh, self._unsharded_dtensor_spec.mesh)
        if dp_mesh is None or tp_mesh is None:
            raise AssertionError(
                "FSDP requires the DP and model parallel TP/EP mesh to be not None but got: \n"
                f"DP's mesh: {dp_mesh}\nTP/EP's mesh: {tp_mesh}"
            )
        self._spmd_mesh = DeviceMesh._concatenate([dp_mesh, tp_mesh])
        if len(self._unsharded_dtensor_spec.placements) > 2:
            raise NotImplementedError(
                f"FSDP only supports 1D TP/EP or 2D EP+TP, not {self._unsharded_dtensor_spec.placements}"
            )
        split_factor = self._unsharded_dtensor_spec.num_shards_map[shard_dim]
        if not (2 <= self._spmd_mesh.ndim <= 4):
            raise AssertionError(
                "_spmd_mesh.ndim can only be 2 (FSDP+TP/EP), 3 (FSDP+EP+TP, HSDP+TP/EP), "
                f"or 4 (HSDP+EP+TP) but got {self._spmd_mesh.ndim}."
            )
        if isinstance(self.mesh_info, FSDPMeshInfo):
            dp_shard_tp_placement = (
                (
                    _StridedShard(shard_dim, split_factor=split_factor)
                    if split_factor > 1
                    else fsdp_placement
                ),
                *self._unsharded_dtensor_spec.placements,
            )
        else:  # DDP
            dp_shard_tp_placement = (
                Replicate(),
                *self._unsharded_dtensor_spec.placements,
            )
        self._spmd_placements: tuple[Placement, ...]
        if isinstance(self.mesh_info, HSDPMeshInfo):
            if self.mesh_info.replicate_mesh_dim != 0:
                raise AssertionError(
                    f"Expected replicate_mesh_dim to be 0, got {self.mesh_info.replicate_mesh_dim}"
                )
            self._spmd_placements = (Replicate(),) + dp_shard_tp_placement
        else:
            self._spmd_placements = dp_shard_tp_placement

        self._sharding_spec = DTensorSpec(
            self._spmd_mesh,
            self._spmd_placements,
            tensor_meta=self._unsharded_dtensor_spec.tensor_meta,
        )
        return cast(DTensor, param)._local_tensor