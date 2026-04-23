def _estimate_heading_level(self, text: str, element) -> int:
        """估计标题的层级

        Args:
            text: 标题文本
            element: 元素对象

        Returns:
            int: 标题层级 (0为主标题，1为一级标题, 等等)
        """
        # 1. 通过编号模式判断层级
        for pattern, level in [
            (r'^\s*\d+\.\s+', 1),  # 1. 开头 (一级标题)
            (r'^\s*\d+\.\d+\.\s+', 2),  # 1.1. 开头 (二级标题)
            (r'^\s*\d+\.\d+\.\d+\.\s+', 3),  # 1.1.1. 开头 (三级标题)
            (r'^\s*\d+\.\d+\.\d+\.\d+\.\s+', 4),  # 1.1.1.1. 开头 (四级标题)
        ]:
            if re.match(pattern, text):
                return level

        # 2. 检查是否是常见的主要章节标题
        lower_text = text.lower()
        main_sections = [
            'abstract', 'introduction', 'background', 'methodology',
            'results', 'discussion', 'conclusion', 'references'
        ]
        for section in main_sections:
            if section in lower_text:
                return 1  # 主要章节为一级标题

        # 3. 根据文本特征判断
        if text.isupper():  # 全大写文本可能是章标题
            return 1

        # 4. 通过元数据判断层级
        if hasattr(element, 'metadata') and element.metadata:
            try:
                # 根据字体大小判断层级
                font_size = getattr(element.metadata, 'font_size', None)
                if font_size is not None:
                    if font_size > 18:  # 假设主标题字体最大
                        return 0
                    elif font_size > 16:
                        return 1
                    elif font_size > 14:
                        return 2
                    else:
                        return 3
            except (AttributeError, TypeError):
                pass

        # 默认为二级标题
        return 2