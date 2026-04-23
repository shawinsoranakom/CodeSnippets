def _check_equals(self, other: object, skip_shapes: bool = False) -> bool:
        if not (
            isinstance(other, DTensorSpec)
            and self.mesh == other.mesh
            and self.placements == other.placements
            and self.shard_order == other.shard_order
        ):
            return False
        if self.tensor_meta is None or other.tensor_meta is None:
            return self.tensor_meta == other.tensor_meta

        if skip_shapes:
            return self.tensor_meta.dtype == other.tensor_meta.dtype
        return (
            self.tensor_meta.shape == other.tensor_meta.shape  # type: ignore[union-attr]
            and self.tensor_meta.stride == other.tensor_meta.stride  # type: ignore[union-attr]
            and self.tensor_meta.dtype == other.tensor_meta.dtype  # type: ignore[union-attr]
        )