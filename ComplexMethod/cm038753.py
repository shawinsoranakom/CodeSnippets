def get_mm_item_sampling_params(
        self,
        base_items_per_request: int,
        num_mm_items_range_ratio: float,
        limit_mm_per_prompt: dict[str, int],
        bucket_config: dict[tuple[int, int, int], float],
    ) -> tuple[int, int, dict[str, int], dict[tuple[int, int, int], float]]:
        """
        Get the sampling parameters for the multimodal items.
        """
        # Enforce num_mm_items_range_ratio <= 1
        if not (0.0 <= num_mm_items_range_ratio <= 1.0):
            raise ValueError("num_mm_items_range_ratio must be in [0, 1].")

        # Ensure modalities to sample are in limit_mm_per_prompt
        for k, v in bucket_config.items():
            # get modality from bucket config
            modality = self.map_config_to_modality(k)
            if modality not in limit_mm_per_prompt:
                raise ValueError(
                    f"Modality {modality} is not in "
                    f"limit_mm_per_prompt: "
                    f"{limit_mm_per_prompt.keys()}"
                )

        # Remove zero probability entries
        # and normalize bucket config to sum to 1
        bucket_config = self.normalize_bucket_config(bucket_config)
        logger.info(
            "Normalized bucket config: %s",
            bucket_config,
        )
        # Only consider limit per prompt for modalities in bucket config
        allowed_modalities = {self.map_config_to_modality(cfg) for cfg in bucket_config}
        limit_mm_per_prompt = {
            k: v for k, v in limit_mm_per_prompt.items() if k in allowed_modalities
        }
        if not limit_mm_per_prompt:
            raise ValueError("No valid limits for modalities present in bucket_config.")

        logger.info(
            "Updated mm-limit-per-prompt: %s",
            limit_mm_per_prompt,
        )

        # Get max and min num mm items and ensure
        # it is at most the sum of limit_mm_per_prompt for all modalities
        max_num_mm_items = min(
            sum(limit_mm_per_prompt.values()),
            math.ceil(base_items_per_request * (1 + num_mm_items_range_ratio)),
        )
        # Ensure min num mm items is at least 0
        min_num_mm_items = max(
            0, math.floor(base_items_per_request * (1 - num_mm_items_range_ratio))
        )
        # Raise error if min num mm items is greater than max num mm items
        if min_num_mm_items > max_num_mm_items:
            raise ValueError(
                f"Min num mm items is greater than max mm items: "
                f"{min_num_mm_items} > {max_num_mm_items}"
            )

        logger.info(
            "Sampling number of multimodal items from [%s, %s]",
            min_num_mm_items,
            max_num_mm_items,
        )

        return (
            min_num_mm_items,
            max_num_mm_items,
            limit_mm_per_prompt,
            bucket_config,
        )