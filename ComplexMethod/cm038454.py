def _fill_blocks(self, group_idx: int, block_ids: list[int], num_tokens: int):
        """
        Fill specified blocks with dummy non-zero values for a specific KV cache group.

        Args:
            group_idx: The KV cache group index to fill
            block_ids: List of block IDs to fill in this group
            num_tokens: Total number of tokens to fill across these blocks
        """
        if not block_ids:
            return

        assert self.kv_caches is not None
        assert self.group_to_layers is not None

        # Get the layers that belong to this group
        layer_names = self.group_to_layers.get(group_idx, [])

        # Fill only the layers in this group
        for layer_name in layer_names:
            if layer_name not in self.kv_caches:
                logger.warning(
                    "DecodeBenchConnector: Layer %s not found in KV caches", layer_name
                )
                continue

            kv_cache = self.kv_caches[layer_name]

            # Convert block_ids to tensor on device
            block_ids_tensor = torch.tensor(
                block_ids, dtype=torch.long, device=kv_cache.device
            )

            # Filter invalid block IDs
            valid_mask = block_ids_tensor < kv_cache.shape[0]
            valid_block_ids = block_ids_tensor[valid_mask]

            if len(valid_block_ids) == 0:
                continue

            # Create fill values - either constant or random
            block_shape = kv_cache.shape[1:]
            if self.fill_std > 0:
                # Random normal sampling
                fill_values = torch.normal(
                    mean=self.fill_mean,
                    std=self.fill_std,
                    size=(len(valid_block_ids),) + block_shape,
                    dtype=kv_cache.dtype,
                    device=kv_cache.device,
                )
            else:
                # Constant fill value
                fill_values = torch.full(
                    (len(valid_block_ids),) + block_shape,
                    self.fill_mean,
                    dtype=kv_cache.dtype,
                    device=kv_cache.device,
                )

            # Batch fill operation
            kv_cache[valid_block_ids] = fill_values

        logger.debug(
            "DecodeBenchConnector: Filled %d blocks in group %d with %s values "
            "(mean=%.3f, std=%.3f)",
            len(block_ids),
            group_idx,
            "random" if self.fill_std > 0 else "constant",
            self.fill_mean,
            self.fill_std,
        )