def _build_text_with_equations_and_hyperlinks(
        self,
        paragraph_elements: list[
            tuple[str, Optional[Formatting], Optional[Union[AnyUrl, Path, str]]]
        ],
        text_with_equations: str,
        equations: list,
    ) -> str:
        """
        构建同时包含公式、超链接和字体样式的文本。

        Args:
            paragraph_elements: 段落元素列表，包含格式和超链接信息
            text_with_equations: 包含公式标记的原始文本
            equations: 公式列表

        Returns:
            str: 包含公式标记、超链接格式和字体样式的文本
        """
        if not equations:
            # 没有公式，直接返回带超链接和样式的文本
            return self._build_text_from_elements(paragraph_elements)

        # 检查是否有超链接
        has_hyperlink = any(
            hyperlink is not None and str(hyperlink).strip() not in ("", ".")
            for _, _, hyperlink in paragraph_elements
        )

        # 检查是否有字体样式
        has_style = any(
            fmt is not None and (fmt.bold or fmt.italic or fmt.underline or fmt.strikethrough)
            for _, fmt, _ in paragraph_elements
        )

        if not has_hyperlink and not has_style:
            # 没有超链接也没有样式，直接返回带公式的文本
            return text_with_equations

        # 同时有公式和超链接/样式，需要合并处理
        # 策略：在带公式的文本基础上，将样式/超链接标记插入到正确的位置

        # 0. 拆分 text_with_equations，获取各非公式片段，用于解决跨公式边界的元素合并问题
        eq_split_pattern = re.compile(r'<eq>.*?</eq>', re.DOTALL)
        non_eq_segments = eq_split_pattern.split(text_with_equations)

        # 在公式边界处重新拆分段落元素，避免单个元素跨越多个非公式片段
        paragraph_elements = self._split_paragraph_elements_at_eq_boundaries(
            paragraph_elements, non_eq_segments
        )

        # 1. 记录每个元素的原始文本和对应的格式化结果
        element_mappings = []
        for text, format_obj, hyperlink in paragraph_elements:
            if text:
                style_str = self._get_style_str_from_format(format_obj)
                formatted_text = self._format_text_with_hyperlink(text, hyperlink, style_str)
                element_mappings.append((text, formatted_text))

        # 2. 在 text_with_equations 中定位每个元素的原始文本，然后替换为格式化后的文本
        result_text = text_with_equations
        for original_text, formatted_text in element_mappings:
            if original_text != formatted_text:
                # 只有当文本被格式化（添加样式或超链接）时才需要替换
                result_text = self._replace_text_outside_equations(
                    result_text, original_text, formatted_text
                )

        return result_text