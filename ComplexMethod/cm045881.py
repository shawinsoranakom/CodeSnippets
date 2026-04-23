def _format_text_with_hyperlink(
        cls,
        text: str,
        hyperlink: Optional[Union[AnyUrl, Path, str]],
        style_str: Optional[str] = None,
    ) -> str:
        """
        将文本和超链接格式化，支持字体样式标记。

        无超链接时：有样式包裹为 <text style="...">文本</text>，无样式直接返回文本。
        有超链接时：格式化为 <hyperlink><text [style="..."]>文本</text><url>链接</url></hyperlink>。

        Args:
            text: 文本内容
            hyperlink: 超链接地址
            style_str: 样式字符串（如 "bold,italic"），无样式时为 None

        Returns:
            str: 格式化后的文本
        """
        if not text:
            return text

        # 检查超链接是否有效（非空）
        if hyperlink is None:
            # 无超链接：只有有样式时才包裹 <text> 标签
            if style_str:
                return f'<text style="{style_str}">{text}</text>'
            return text

        hyperlink_str = str(hyperlink)
        if not hyperlink_str or hyperlink_str.strip() == "" or hyperlink_str == ".":
            if style_str:
                return f'<text style="{style_str}">{text}</text>'
            return text

        # 有超链接：构建 <text> 标签（含可选样式）
        if style_str:
            text_tag = f'<text style="{style_str}">{text}</text>'
        else:
            text_tag = f'<text>{text}</text>'

        return f"<hyperlink>{text_tag}<url>{hyperlink_str}</url></hyperlink>"