def process_media(
        self,
        media: Image.Image,
        num_tokens_available: int,
    ) -> tuple[DynamicResolutionParams, int]:
        """Process a single media item and return its parameters.

        Args:
            media: The media item to process
            num_tokens_available: Number of tokens available for this media
        Returns:
            DynamicResolutionParams for the media
        """
        current_num_tokens_available = num_tokens_available
        assert isinstance(media, Image.Image), (
            "Dynamic resolution is only supported for image media"
        )
        orig_width, orig_height = media.width, media.height
        closest_patch_height = round(orig_height / self._patch_size + 0.5)
        closest_patch_width = round(orig_width / self._patch_size + 0.5)
        patches = closest_patch_height * closest_patch_width

        factor = min(
            math.sqrt(current_num_tokens_available / patches), self._factor_max
        )
        target_patch_height = math.floor(factor * closest_patch_height)
        target_patch_width = math.floor(factor * closest_patch_width)

        # Consider self._min_num_patches if > current_num_tokens_available.
        if (
            current_num_tokens_available > self._min_num_patches
            and target_patch_height * target_patch_width < self._min_num_patches
        ):
            up_factor = math.sqrt(
                self._min_num_patches / (target_patch_height * target_patch_width)
            )
            target_patch_height = math.ceil(up_factor * target_patch_height)
            target_patch_width = math.ceil(up_factor * target_patch_width)

        # Round patch grid to be divisible by 2 (pixel-shuffle OR conv-merging)
        # or by 4 when BOTH are enabled (two successive 2x reductions)
        if self.PIXEL_SHUFFLE or self.CONV_MERGING:
            required_divisor = 4 if (self.PIXEL_SHUFFLE and self.CONV_MERGING) else 2

            rem_h = target_patch_height % required_divisor
            if rem_h != 0:
                inc_h = required_divisor - rem_h
                if (
                    target_patch_height + inc_h
                ) * target_patch_width <= current_num_tokens_available:
                    target_patch_height += inc_h
                else:
                    target_patch_height = max(
                        required_divisor, target_patch_height - rem_h
                    )

            rem_w = target_patch_width % required_divisor
            if rem_w != 0:
                inc_w = required_divisor - rem_w
                if (
                    target_patch_height * (target_patch_width + inc_w)
                    <= current_num_tokens_available
                ):
                    target_patch_width += inc_w
                else:
                    target_patch_width = max(
                        required_divisor, target_patch_width - rem_w
                    )

        # Calculate embeddings for the main dynamic resolution image
        num_embeddings = self._get_num_embeddings(
            target_patch_width * self._patch_size,
            target_patch_height * self._patch_size,
        )

        token_count = target_patch_width * target_patch_height

        # Add thumbnail embeddings if enabled and image area is below threshold
        num_tiles = 1  # Base dynamic resolution image

        return self.DynamicResolutionParams(
            media=media,
            num_tiles=num_tiles,
            num_embeddings=num_embeddings,
            patch_size=(target_patch_width, target_patch_height),
        ), token_count