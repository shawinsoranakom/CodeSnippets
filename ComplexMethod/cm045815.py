def _promote_level3_text_blocks(
        self,
        slide_blocks: list[dict],
        body_font_size_pt: Optional[float],
    ) -> None:
        if body_font_size_pt is None:
            return

        level2_font_sizes = sorted(
            {
                block[_EFFECTIVE_FONT_SIZE_KEY]
                for block in slide_blocks
                if (
                    block.get("type") == BlockType.TITLE
                    and block.get("level") == 2
                    and block.get(_EFFECTIVE_FONT_SIZE_KEY) is not None
                )
            },
            reverse=True,
        )
        if not level2_font_sizes:
            return

        level2_font_size_pt = level2_font_sizes[0]
        level3_font_sizes = sorted(
            {
                block[_EFFECTIVE_FONT_SIZE_KEY]
                for block in slide_blocks
                if (
                    block.get("type") == BlockType.TEXT
                    and block.get(_EFFECTIVE_ALL_BOLD_KEY, False)
                    and block.get(_EFFECTIVE_FONT_SIZE_KEY) is not None
                    and block[_EFFECTIVE_FONT_SIZE_KEY] < level2_font_size_pt
                )
            },
            reverse=True,
        )
        if not level3_font_sizes:
            return

        level3_font_size_pt = level3_font_sizes[0]
        if level3_font_size_pt < body_font_size_pt + 2:
            return
        if level2_font_size_pt < level3_font_size_pt + 2:
            return

        for block in slide_blocks:
            if (
                block.get("type") == BlockType.TEXT
                and block.get(_EFFECTIVE_ALL_BOLD_KEY, False)
                and block.get(_EFFECTIVE_FONT_SIZE_KEY) == level3_font_size_pt
            ):
                block["type"] = BlockType.TITLE
                block["level"] = 3