def _estimate_title_level(self, title_element, all_elements) -> int:
        """估计标题的层级"""
        title_text = str(title_element).strip()

        # 通过标题文本中的编号格式判断层级
        # 查找诸如 "1."、"1.1"、"1.1.1" 等模式
        level_patterns = [
            (r'^(\d+\.?\s+)', 1),  # 1. 或 1 开头为一级标题
            (r'^(\d+\.\d+\.?\s+)', 2),  # 1.1. 或 1.1 开头为二级标题
            (r'^(\d+\.\d+\.\d+\.?\s+)', 3),  # 1.1.1. 或 1.1.1 开头为三级标题
            (r'^(\d+\.\d+\.\d+\.\d+\.?\s+)', 4),  # 1.1.1.1. 或 1.1.1.1 开头为四级标题
        ]

        for pattern, level in level_patterns:
            if re.match(pattern, title_text):
                return level

        # 检查标题是否是常见的主要章节标题
        main_sections = {'abstract', 'introduction', 'method', 'result', 'discussion', 'conclusion', 'references'}
        if self._identify_section_type(title_text) in main_sections:
            return 1

        # 检查字体大小（如果元数据中有）
        if hasattr(title_element, 'metadata') and title_element.metadata:
            try:
                # 尝试获取字体大小信息
                font_size = getattr(title_element.metadata, 'font_size', None)
                if font_size is not None:
                    # 根据字体大小确定层级（较大字体为较低层级）
                    if font_size > 16:
                        return 1
                    elif font_size > 14:
                        return 2
                    else:
                        return 3
            except (AttributeError, TypeError):
                pass

        # 默认为1级标题
        return 1