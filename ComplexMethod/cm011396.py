def __post_init__(self) -> None:
        if not isinstance(self.placements, tuple):
            self.placements = tuple(self.placements)
        if self.use_strided_shard_as_shard_order is None:
            if any(isinstance(p, _StridedShard) for p in self.placements):
                self.use_strided_shard_as_shard_order = True
            else:
                self.use_strided_shard_as_shard_order = False
        if self.use_strided_shard_as_shard_order:
            if self.shard_order is not None:
                raise ValueError(
                    "DTensorSpec doesn't allow specify shard_order when "
                    "use_strided_shard_as_shard_order is True. This may result "
                    "in conflicting shard order."
                )
        else:
            if self.shard_order is None:
                self.shard_order = self.compute_default_shard_order(self.placements)

        self._hash: int | None = None