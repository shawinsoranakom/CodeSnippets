def _analyze_split(self, cmd: Split) -> list[InputDim]:
        """Fill self.shard_allowed for Split; return shardable input dims."""
        from torch.fx.experimental.symbolic_shapes import guard_or_false, guard_or_true

        in_dims = self._analyze_dim(cmd.input_dim)
        if len(in_dims) == 0:
            return []
        in_dim = in_dims[0]
        out_size = cmd.group_shape[cmd.split_id]
        shard_mesh_dim, input_src_placement = self._find_shard_for_split(
            in_dim.input_dim, cmd, self.input_src_placements
        )
        # split_id == 0 sets the base shard_allowed for this input dim.
        # Later split_ids (processed in subsequent rule iterations) refine
        # individual mesh_dim entries via the _StridedShard branch below.
        if cmd.split_id == 0:
            self.shard_allowed[in_dim.input_dim] = [
                guard_or_false(out_size % mesh_dim_size == 0)
                for mesh_dim_size in self.mesh_sizes
            ]
            plain_mesh_dim, _ = self._find_plain_shard(in_dim)
            # Non-strict silently redistributes via shard_allowed=False above;
            # strict raises so the user knows to redistribute before view().
            if self.strict_view and plain_mesh_dim is not None:
                if not self.shard_allowed[in_dim.input_dim][plain_mesh_dim]:
                    raise RuntimeError(
                        f"Cannot unflatten unevenly sharded tensor: "
                        f"output dimension {cmd.split_id} (size {out_size}) "
                        f"is not evenly divisible by mesh dimension "
                        f"{plain_mesh_dim} (size {self.mesh_sizes[plain_mesh_dim]}). "
                        f"Please redistribute the tensor before this operation."
                    )
        if shard_mesh_dim is not None and isinstance(
            input_src_placement, _StridedShard
        ):
            # The last split dim doesn't require even divisibility because
            # its local size is inferred: local_last = local_flat / product
            # of earlier dims, and DTensor handles uneven local sizes.
            # Non-last dims must be evenly divisible because they appear as
            # fixed sizes in the local reshape — uneven division would make
            # the stride pattern inconsistent across devices.
            # E.g. [12] → [3, 4], _StridedShard targeting dim 1 (last),
            # mesh=3: 4%3≠0, but local shapes [3,2],[3,1],[3,1] are valid.
            is_last_split_dim = cmd.split_id == len(cmd.group_shape) - 1
            if (
                self.strict_view
                and not is_last_split_dim
                and guard_or_true(out_size % self.mesh_sizes[shard_mesh_dim] != 0)
            ):
                raise RuntimeError(
                    f"Cannot unflatten unevenly sharded tensor: "
                    f"output dimension {cmd.split_id} (size {out_size}) "
                    f"is not evenly divisible by mesh dimension {shard_mesh_dim} "
                    f"(size {self.mesh_sizes[shard_mesh_dim]}). "
                    f"Please redistribute the tensor before this operation."
                )
            # Prevents _find_shard_for_split from matching this mesh dim
            # again for a later split_id of the same Split group.
            self.matched_strided_mesh_dims.add(shard_mesh_dim)
            if in_dim.input_dim in self.shard_allowed:
                self.shard_allowed[in_dim.input_dim][shard_mesh_dim] = (
                    guard_or_false(out_size % self.mesh_sizes[shard_mesh_dim] == 0)
                    or is_last_split_dim
                )
        # Only split_id==0 returns the input dim for input_to_output_tensor_dims.
        # Later split_ids refine shard_allowed above but return [] — their
        # output dims are linked via the root-input-dim chase in analyze().
        return [in_dim] if cmd.split_id == 0 else []