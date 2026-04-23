def validate_shard_id(self, loaded_shard_id: int | tuple[int, ...] | None):
        if loaded_shard_id is None:
            return
        if isinstance(loaded_shard_id, tuple):
            for idx in loaded_shard_id:
                if not (0 <= idx < len(self.output_sizes)):
                    raise ValueError(
                        f"Shard id index {idx} should be between 0 and "
                        f"{len(self.output_sizes) - 1}. Got shard id {loaded_shard_id}."
                    )
            if len(loaded_shard_id) > 1 and any(
                b - a != 1 for a, b in zip(loaded_shard_id[:-1], loaded_shard_id[1:])
            ):
                raise ValueError(
                    "Shard id with multiple indices should be consecutive. "
                    f"Got shard id {loaded_shard_id}."
                )
            return
        elif isinstance(loaded_shard_id, int):
            if loaded_shard_id < 0 or loaded_shard_id >= len(self.output_sizes):
                raise ValueError(
                    f"Shard id should be between 0 and {len(self.output_sizes) - 1}. "
                    f"Got shard id {loaded_shard_id}."
                )
            return
        raise ValueError("This line should not be reached")