def _find_keep_ss_dim(
        self,
        tgt_shard_dims: list[int],
        p: _StridedShard,
        mesh_dim: int,
    ) -> int | None:
        """Find an output dim where SS stays as SS.

        Returns the first output dim whose Split can accommodate the combined
        sharding (mesh_size * split_factor), or ``None`` if no dim fits.
        """
        total_shard = self.mesh_sizes[mesh_dim] * p.split_factor
        if self.global_input_shape[p.dim] % total_shard != 0:
            return None
        shard_size = self.global_input_shape[p.dim] // total_shard
        for candidate_dim in tgt_shard_dims:
            cmd = self.rule[candidate_dim]
            if isinstance(cmd, Split):
                inner_size = math.prod(cmd.group_shape[cmd.split_id + 1 :])
                # When a Split wraps a Flatten, the per-shard chunk covers
                # the sharded dim plus trailing dims flattened together.
                trailing_size = 1
                if isinstance(cmd.input_dim, Flatten):
                    found = False
                    for flat_dim in cmd.input_dim.input_dims:
                        if not isinstance(flat_dim, InputDim):
                            raise AssertionError(
                                f"Expected InputDim, got {type(flat_dim)}"
                            )
                        if flat_dim.input_dim == p.dim:
                            found = True
                        elif found:
                            trailing_size *= self.global_input_shape[flat_dim.input_dim]
                flattened_shard_size = shard_size * trailing_size
                if (
                    flattened_shard_size >= inner_size
                    and flattened_shard_size % inner_size == 0
                ):
                    return candidate_dim
        return None