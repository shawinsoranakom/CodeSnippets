def _rewrite_plain_shard(
        self,
        p: Shard,
        mesh_dim: int,
        placements: Sequence[Placement],
        strided_shard_claimed_dims: set[ClaimedDim],
        local_tensor_shapes: list[int],
        input_to_output_tensor_dims: dict[int, list[int]],
    ) -> tuple[Placement, list[int]]:
        """Given a plain Shard(dim=X) input placement on a specific mesh dim,
        determine what output placement it maps to after the view op.

        For identity and unflatten, produces Shard on the output dim.  For
        flatten, Shard on the first flattened dim stays Shard, while Shard on
        a non-first dim produces _StridedShard (consumed later by
        _rewrite_strided_shard).

        Returns the output placement and a new local_tensor_shapes with this
        mesh dim's division applied.
        """
        # Output dims that input dim p.dim maps to, filtering out any
        # already claimed by _StridedShard rewriting on earlier mesh dims.
        tgt_shard_dims = [
            d
            for d in input_to_output_tensor_dims[p.dim]
            if ClaimedDim(p.dim, d) not in strided_shard_claimed_dims
        ]
        if len(tgt_shard_dims) == 0:
            raise AssertionError(
                f"No output dim available for Shard(dim={p.dim}) on mesh dim "
                f"{mesh_dim}. All output dims already claimed by earlier mesh dims."
            )
        if len(tgt_shard_dims) == 1:
            tgt_shard_dim = tgt_shard_dims[0]
        else:
            # Unflatten: one input dim maps to multiple output dims
            # (e.g. (24,) → (2, 3, 4) gives 3 splits). Plain Shard
            # always targets the split_id=0 output dim.
            tgt_shard_dim = next(
                (
                    d
                    for d in tgt_shard_dims
                    if isinstance(self.rule[d], Split)
                    and cast(Split, self.rule[d]).split_id == 0
                ),
                None,
            )
            if tgt_shard_dim is None:
                raise AssertionError(
                    f"No Split(split_id=0) found among unclaimed output dims "
                    f"{tgt_shard_dims} for Shard(dim={p.dim}) on mesh dim {mesh_dim}."
                )
        cmd = self.rule[tgt_shard_dim]
        if isinstance(cmd, Split) and isinstance(cmd.input_dim, Flatten):
            first_dim = cmd.input_dim.input_dims[0]
            if isinstance(first_dim, InputDim) and p.dim != first_dim.input_dim:
                raise RuntimeError(
                    f"Shard(dim={p.dim}) through Split(Flatten(...), {cmd.group_shape}) "
                    f"is not supported yet for non-first flatten dims."
                )
        if isinstance(cmd, (Split, InputDim)):
            # Split/InputDim: 1:1 dim mapping, sharding transfers directly.
            # Flatten needs stride computation below (multiple dims merge).
            new_shapes = list(local_tensor_shapes)
            new_shapes[p.dim] //= self.mesh_sizes[mesh_dim]
            return Shard(tgt_shard_dim), new_shapes
        if not isinstance(cmd, Flatten):
            raise AssertionError(f"Expected Flatten, got {type(cmd)}")
        first_dim = cmd.input_dims[0]
        last_dim = cmd.input_dims[-1]
        if not isinstance(first_dim, InputDim):
            raise AssertionError(f"Expected InputDim, got {type(first_dim)}")
        if not isinstance(last_dim, InputDim):
            raise AssertionError(f"Expected InputDim, got {type(last_dim)}")
        input_start_idx = first_dim.input_dim
        if p.dim == input_start_idx:
            output_placement: Placement = Shard(tgt_shard_dim)
        else:
            split_factor = math.prod(local_tensor_shapes[input_start_idx : p.dim])
            output_placement = _StridedShard(tgt_shard_dim, split_factor=split_factor)
        # Uneven sharding on a non-last flatten dim breaks _StridedShard:
        # split_factor (number of groups) must be the same on all devices,
        # but uneven division of a non-last dim makes group count vary.
        # E.g. [3,4]→[12] Shard(0) mesh=2: device 0 has 2 groups of 4,
        # device 1 has 1 group of 4 — no consistent split_factor.
        # The last dim is exempt: only group *size* varies, not count.
        flatten_end = last_dim.input_dim + 1
        if local_tensor_shapes[p.dim] % self.mesh_sizes[
            mesh_dim
        ] != 0 and not self._is_last_shard_in_flatten_range(
            mesh_dim, placements, input_start_idx, flatten_end
        ):
            raise RuntimeError(
                f"Cannot shard unevenly distributed tensor: "
                f"dimension {p.dim} (size {local_tensor_shapes[p.dim]}) "
                f"is not evenly divisible by mesh dimension "
                f"{mesh_dim} (size {self.mesh_sizes[mesh_dim]}). "
                f"Please redistribute the tensor before this operation."
            )
        new_shapes = list(local_tensor_shapes)
        new_shapes[p.dim] //= self.mesh_sizes[mesh_dim]
        return output_placement, new_shapes