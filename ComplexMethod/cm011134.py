def _init_sharding_spec_spmd(
        self,
        param: nn.Parameter,
        fsdp_placement: Shard,
        shard_dim: int,
    ) -> torch.Tensor:
        """SPMD path: param is a DTensor on the full SPMD mesh."""
        self._unsharded_dtensor_spec = cast(DTensor, param)._spec
        spmd_mesh = self._unsharded_dtensor_spec.mesh
        dp_dim_names = self.mesh_info.dp_mesh_dims
        if dp_dim_names is None:
            raise AssertionError("dp_dim_names must not be None for SPMD mesh")
        if spmd_mesh.mesh_dim_names is None:
            raise AssertionError("spmd_mesh.mesh_dim_names must not be None")
        if (
            self.mesh_info.spmd_mesh is not None
            and spmd_mesh is not self.mesh_info.spmd_mesh
        ):
            raise ValueError(
                "Expected param's DTensor mesh to be the same mesh passed "
                "to fully_shard, but got different mesh objects"
            )

        dp_shard_indices = [
            spmd_mesh.mesh_dim_names.index(n) for n in dp_dim_names.shard_names
        ]

        orig_placements = self._unsharded_dtensor_spec.placements
        for idx in dp_shard_indices:
            if not isinstance(orig_placements[idx], Replicate):
                raise ValueError(
                    f"Expected Replicate() on DP shard dim "
                    f"'{spmd_mesh.mesh_dim_names[idx]}' (index {idx}) "
                    f"but got {orig_placements[idx]}"
                )
        dp_replicate_indices = []
        for rep_name in dp_dim_names.replicate_names:
            rep_idx = spmd_mesh.mesh_dim_names.index(rep_name)
            dp_replicate_indices.append(rep_idx)
            if not isinstance(orig_placements[rep_idx], Replicate):
                raise ValueError(
                    f"Expected Replicate() on DP replicate dim "
                    f"'{spmd_mesh.mesh_dim_names[rep_idx]}' (index {rep_idx}) "
                    f"but got {orig_placements[rep_idx]}"
                )

        # Cache DP dim indices so _get_grad_inner_tensor can skip
        # redistribution on DP dims and let FSDP's reduce-scatter handle them.
        self._dp_dim_indices: frozenset[int] = frozenset(
            dp_shard_indices + dp_replicate_indices
        )

        new_placements = list(orig_placements)
        for dp_idx in dp_shard_indices:
            # split_factor = number of non-DP shards on shard_dim from
            # mesh dims with higher index (the "right-side" dims that
            # _StridedShard needs to interleave with)
            sf = 1
            for j in range(dp_idx + 1, spmd_mesh.ndim):
                p = orig_placements[j]
                if isinstance(p, (Shard, _StridedShard)) and p.dim == shard_dim:
                    sf *= spmd_mesh.size(j)
            new_placements[dp_idx] = (
                _StridedShard(shard_dim, split_factor=sf) if sf > 1 else fsdp_placement
            )

        self._spmd_mesh = spmd_mesh
        self._spmd_placements: tuple[Placement, ...] = tuple(new_placements)
        self._sharding_spec = DTensorSpec(
            self._spmd_mesh,
            self._spmd_placements,
            tensor_meta=self._unsharded_dtensor_spec.tensor_meta,
        )
        return cast(DTensor, param)._local_tensor