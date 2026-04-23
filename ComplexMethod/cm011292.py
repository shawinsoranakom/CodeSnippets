def get_diff(self, other: _TensorMeta) -> list[str]:
        """Return field-by-field differences, including DTensor-specific fields.

        Args:
            other: Metadata to compare against.

        Returns:
            List of human-readable difference strings (empty if equal).
        """
        if self == other:
            return []

        # Get base class differences (compares local shape/stride/dtype/requires_grad)
        # NOTE: Use explicit class call instead of super() because
        # @dataclass(slots=True) on both parent and child can break super().
        diffs = _TensorMeta.get_diff(self, other)

        # Add DTensor-specific comparisons if other is also _DTensorMeta
        if isinstance(other, _DTensorMeta):
            if self.global_shape != other.global_shape:
                diffs.append(
                    f"global_shape mismatch: {self.global_shape} vs {other.global_shape}"
                )
            if self.global_stride != other.global_stride:
                diffs.append(
                    f"global_stride mismatch: {self.global_stride} vs {other.global_stride}"
                )
            if self.placements != other.placements:
                diffs.append(
                    f"placements mismatch: {self.placements} vs {other.placements}"
                )
            if self.mesh_dim_names != other.mesh_dim_names:
                diffs.append(
                    f"mesh_dim_names mismatch: {self.mesh_dim_names} vs {other.mesh_dim_names}"
                )
            if self.mesh_layout != other.mesh_layout:
                diffs.append(
                    f"mesh_layout mismatch: {self.mesh_layout} vs {other.mesh_layout}"
                )
        else:
            diffs.append("type: _DTensorMeta vs _TensorMeta")

        return diffs