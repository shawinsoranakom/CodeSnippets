def compute_params(
        self,
        media_list: list[Image.Image],
        num_tokens_available: int,
    ) -> list[DynamicResolutionParams]:
        """Compute parameters for all media with iterative token budgeting.

        Args:
            media_list: List of media items to process
            num_tokens_available: Total number of tokens available across all media
        Returns:
            List of ImageTilingParams for each media item
        """
        num_tokens_available = (
            num_tokens_available
            * (4 if self.PIXEL_SHUFFLE else 1)
            * (4 if self.CONV_MERGING else 1)
        )
        # When the number of available token is too small,
        # allow self._min_num_patches per media and let the sample be truncated.
        num_tokens_available = max(
            num_tokens_available, self._min_num_patches * len(media_list)
        )

        # Clip the number of tokens available per media to >min and <max patches.
        num_tokens_available_per_media = [
            int(
                max(
                    min(num_tokens_available, self._max_num_patches),
                    self._min_num_patches,
                )
            )
            for _ in range(len(media_list))
        ]

        # prevent infinite loop in any case
        for _ in range(10):
            # Step 1: Process each media with current token budget
            params = []
            token_counts = []

            for media, tokens_for_media in zip(
                media_list, num_tokens_available_per_media
            ):
                param, token_count = self.process_media(media, tokens_for_media)
                params.append(param)
                token_counts.append(token_count)

            # Step 2: Check if total tokens is within budget
            total_tokens = sum(token_counts)

            if total_tokens <= num_tokens_available:
                # We're within budget, return the params
                return params

            # Step 3: We're over budget, need to scale down
            # Calculate scaling factor to get under budget
            scaling_factor = num_tokens_available / total_tokens

            # Recalculate token budgets for each media based on scaling
            # Each media gets a proportional share of the total budget
            scaled_down_num_tokens_available_per_media = [
                max(self._min_num_patches, int(token_count * scaling_factor))
                for token_count in token_counts
            ]
            scaled_down = any(
                [
                    scaled_down_num_tokens_available_per_media[i]
                    < num_tokens_available_per_media[i]
                    for i in range(len(num_tokens_available_per_media))
                ]
            )
            # If there wasn't scaling down, we're stuck with min_num_patches per media,
            # else try with the scaled down num_tokens_available_per_media.
            if not scaled_down:
                num_tokens_available_per_media = [self._min_num_patches] * len(
                    media_list
                )
            else:
                num_tokens_available_per_media = (
                    scaled_down_num_tokens_available_per_media
                )
        ctx = f"{params=} {total_tokens=} {num_tokens_available=}"
        raise ValueError(
            f"Should be unreachable - `return params` above must be reached: {ctx}"
        )