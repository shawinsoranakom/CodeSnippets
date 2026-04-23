def _get_label_and_level(self, paragraph: Paragraph) -> tuple[str, Optional[int]]:
        """
        获取段落的标签和层级。

        Args:
            paragraph: 段落对象

        Returns:
            tuple[str, Optional[int]]: (标签, 层级) 元组
        """
        if paragraph.style is None:
            return "Normal", None

        label = paragraph.style.style_id
        name = paragraph.style.name

        if label is None:
            return "Normal", None

        for style in self._iter_style_chain(paragraph.style):
            style_label = getattr(style, "style_id", None)
            style_name = getattr(style, "name", None)

            if style_label and ":" in style_label:
                parts = style_label.split(":")
                if len(parts) == 2:
                    return parts[0], self._str_to_int(parts[1], None)

            for candidate in (style_label, style_name):
                if candidate and "heading" in candidate.lower():
                    return self._get_heading_and_level(candidate)

        outline_level = self._get_effective_outline_level(paragraph)
        if outline_level is not None:
            return "Heading", outline_level + 1

        return name, None