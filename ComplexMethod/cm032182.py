def _is_likely_heading(self, text: str, element, index: int, elements) -> bool:
        """判断文本是否可能是标题

        Args:
            text: 文本内容
            element: 元素对象
            index: 元素索引
            elements: 所有元素列表

        Returns:
            bool: 是否可能是标题
        """
        # 1. 检查文本长度 - 标题通常不会太长
        if len(text) > 150:  # 标题通常不超过150个字符
            return False

        # 2. 检查是否匹配标题的数字编号模式
        if any(re.match(pattern, text) for pattern in self.HEADING_PATTERNS):
            return True

        # 3. 检查是否包含常见章节标记词
        lower_text = text.lower()
        for markers in self.SECTION_MARKERS.values():
            if any(marker.lower() in lower_text for marker in markers):
                return True

        # 4. 检查后续内容数量 - 标题后通常有足够多的内容
        if not self._has_sufficient_following_content(index, elements, min_chars=100):
            # 但如果文本很短且以特定格式开头，仍可能是标题
            if len(text) < 50 and (text.endswith(':') or text.endswith('：')):
                return True
            return False

        # 5. 检查格式特征
        # 标题通常是元素的开头，不在段落中间
        if len(text.split('\n')) > 1:
            # 多行文本不太可能是标题
            return False

        # 如果有元数据，检查字体特征（字体大小等）
        if hasattr(element, 'metadata') and element.metadata:
            try:
                font_size = getattr(element.metadata, 'font_size', None)
                is_bold = getattr(element.metadata, 'is_bold', False)

                # 字体较大或加粗的文本更可能是标题
                if font_size and font_size > 12:
                    return True
                if is_bold:
                    return True
            except (AttributeError, TypeError):
                pass

        # 默认返回True，因为元素已被识别为Title类型
        return True