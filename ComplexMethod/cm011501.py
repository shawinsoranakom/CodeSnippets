def _rewrite_strided_shard(
        self,
        p: _StridedShard,
        mesh_dim: int,
        placements: Sequence[Placement],
        strided_shard_claimed_dims: set[ClaimedDim],
        local_tensor_shapes: list[int],
        input_to_output_tensor_dims: dict[int, list[int]],
    ) -> tuple[Placement, list[int]]:
        """Rewrite _StridedShard placement to target the correct output dim.

        _StridedShard inputs arise from a prior flatten on a non-first dim
        (produced by _rewrite_plain_shard above).  The interesting case is
        unflatten (Split rule): the split_factor may resolve to contiguous
        sharding (producing Shard) or stay as _StridedShard.  For
        identity/flatten rules, falls through to the fallback and keeps the
        placement as-is.

        Returns the output placement and a new local_tensor_shapes with this
        mesh dim's division applied.
        """
        tgt_shard_dims = [
            d
            for d in input_to_output_tensor_dims[p.dim]
            if ClaimedDim(p.dim, d) not in strided_shard_claimed_dims
        ]
        # Phase 1: resolve SS → Shard.  If an output dim's Split has a
        # group_shape prefix matching the split_factor, the strided pattern
        # is fully captured by the Split, so SS simplifies to Shard.
        # E.g. unflatten (6, 4) → (2, 3, 4) with SS(0, sf=2) on mesh (3):
        # sf=2 means 2 groups of contiguous data in dim 0.  Split into
        # (2, 3, 4) gives group_shape=(2, 3); prod(group_shape[:1])=2==sf,
        # so the strided pattern lands exactly on output dim 1 → Shard(1).
        for candidate_dim in tgt_shard_dims:
            cmd = self.rule[candidate_dim]
            if isinstance(cmd, Split):
                expected_sf = self._expected_split_factor(
                    cmd, p.dim, mesh_dim, placements
                )
                if expected_sf != p.split_factor:
                    continue
                strided_shard_claimed_dims.add(ClaimedDim(p.dim, candidate_dim))
                new_shapes = list(local_tensor_shapes)
                new_shapes[p.dim] //= self.mesh_sizes[mesh_dim]
                return Shard(candidate_dim), new_shapes

        # Phase 2: keep SS as SS.  Phase 1 is tried first because we prefer
        # resolving to the simpler Shard when possible.
        tgt_shard_dim = self._find_keep_ss_dim(tgt_shard_dims, p, mesh_dim)

        if tgt_shard_dim is None:
            if self.strict_view and any(
                isinstance(self.rule[d], Split) for d in tgt_shard_dims
            ):
                raise RuntimeError(
                    f"Cannot unflatten tensor with _StridedShard placement: "
                    f"split_factor={p.split_factor} does not match any output "
                    f"dimension. This typically means the _StridedShard placement "
                    f"was constructed with a split_factor that is incompatible "
                    f"with the unflatten shape. Please redistribute the tensor "
                    f"before this operation."
                )
            if len(tgt_shard_dims) == 0:
                raise AssertionError(
                    f"No unclaimed output dims for _StridedShard(dim={p.dim}) "
                    f"on mesh dim {mesh_dim}."
                )
            # Fallback for identity/flatten: tgt_shard_dims has exactly one
            # element, so [0] is correct.  For Split rules this is unreachable
            # in practice — the analysis phase rejects mismatched split_factors
            # via shard_allowed, forcing redistribution before we get here.
            tgt_shard_dim = tgt_shard_dims[0]
        new_shapes = list(local_tensor_shapes)
        new_shapes[p.dim] //= self.mesh_sizes[mesh_dim]
        return _StridedShard(tgt_shard_dim, split_factor=p.split_factor), new_shapes