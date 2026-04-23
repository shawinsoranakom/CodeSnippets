def _verify_shard_order(self, shard_order: ShardOrder) -> None:
        """Verify that the shard_order is valid and matches the placements."""
        total_shard = 0
        if any(isinstance(p, _StridedShard) for p in self.placements):
            # _StridedShard shard_order validation not yet supported;
            # the Shard-only checks below (line 390, 394) would fail.
            return
        prev_tensor_dim = -1
        for entry in shard_order:
            tensor_dim = entry.tensor_dim
            mesh_dims = entry.mesh_dims
            if len(mesh_dims) <= 0:
                raise AssertionError(f"shard_order {shard_order} has empty mesh dim")
            if tensor_dim < 0:
                raise AssertionError(
                    f"shard_order {shard_order} has invalid tensor dim {tensor_dim}"
                )
            if tensor_dim <= prev_tensor_dim:
                raise AssertionError("tensor dim should be sorted in shard_order")
            prev_tensor_dim = tensor_dim
            total_shard += len(mesh_dims)
            for mesh_dim in mesh_dims:
                if not (0 <= mesh_dim < len(self.placements)):
                    raise AssertionError(
                        f"shard_order {shard_order} has invalid mesh dim {mesh_dims}"
                    )
                if self.placements[mesh_dim] != Shard(tensor_dim):
                    raise AssertionError(
                        f"placement[{mesh_dim}] doesn't have a matching shard in shard_order"
                    )
        if total_shard != sum(1 for p in self.placements if isinstance(p, Shard)):
            raise AssertionError