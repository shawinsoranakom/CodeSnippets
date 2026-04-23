def _promote_level2_text_blocks(
        self,
        slide_blocks: list[dict],
        body_font_size_pt: Optional[float],
    ) -> None:
        bold_text_blocks = [
            block
            for block in slide_blocks
            if (
                block.get("type") == BlockType.TEXT
                and block.get(_EFFECTIVE_ALL_BOLD_KEY, False)
                and block.get(_EFFECTIVE_FONT_SIZE_KEY) is not None
            )
        ]
        if not bold_text_blocks:
            return

        bold_font_sizes = sorted(
            {
                block[_EFFECTIVE_FONT_SIZE_KEY]
                for block in bold_text_blocks
            },
            reverse=True,
        )
        level2_font_size_pt = bold_font_sizes[0]
        level2_candidates = [
            block
            for block in bold_text_blocks
            if block[_EFFECTIVE_FONT_SIZE_KEY] == level2_font_size_pt
        ]

        if len(level2_candidates) != 1:
            return

        if (
            body_font_size_pt is not None
            and level2_font_size_pt < body_font_size_pt + 4
        ):
            return

        if (
            len(bold_font_sizes) > 1
            and level2_font_size_pt < bold_font_sizes[1] + 2
        ):
            return

        level2_candidates[0]["type"] = BlockType.TITLE
        level2_candidates[0]["level"] = 2