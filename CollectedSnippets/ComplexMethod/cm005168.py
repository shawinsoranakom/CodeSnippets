def _build_image_tokens(
        self,
        rows: int,
        cols: int,
        tokens_per_tile: int,
        tokens_for_image: int,
        use_thumbnail: bool,
        use_image_special_tokens: bool,
    ) -> str:
        """Build the expanded token string for a single image."""
        parts = []

        if use_image_special_tokens:
            parts.append(self.image_start_token)

        is_multi_tile = rows > 1 or cols > 1
        if is_multi_tile:
            for row in range(rows):
                for col in range(cols):
                    if use_image_special_tokens:
                        parts.append(f"<|img_row_{row + 1}_col_{col + 1}|>")
                    parts.append(self.image_token * tokens_per_tile)

            if use_thumbnail:
                if use_image_special_tokens:
                    parts.append(self.image_thumbnail_token)
                parts.append(self.image_token * tokens_for_image)
        else:
            parts.append(self.image_token * tokens_for_image)

        if use_image_special_tokens:
            parts.append(self.image_end_token)

        return "".join(parts)