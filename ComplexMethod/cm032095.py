def _evaluate_title_candidate(self, text, position, element):
        """评估标题候选项的可能性分数"""
        score = 0

        # 位置因素：越靠前越可能是标题
        score += max(0, 10 - position) * 0.5

        # 长度因素：标题通常不会太短也不会太长
        if 10 <= len(text) <= 150:
            score += 3
        elif len(text) < 10:
            score -= 2
        elif len(text) > 150:
            score -= 3

        # 格式因素
        if text.isupper():  # 全大写可能是标题
            score += 2
        if re.match(r'^[A-Z]', text):  # 首字母大写
            score += 1
        if ':' in text:  # 标题常包含冒号
            score += 1.5

        # 内容因素
        if re.search(r'\b(scaling|learning|model|approach|method|system|framework|analysis)\b', text.lower()):
            score += 2  # 包含常见的学术论文关键词

        # 避免误判
        if re.match(r'^\d+$', text):  # 纯数字
            score -= 10
        if re.search(r'^(http|www|doi)', text.lower()):  # URL或DOI
            score -= 5
        if len(text.split()) <= 2 and len(text) < 15:  # 太短的短语
            score -= 3

        # 元数据因素(如果有)
        if hasattr(element, 'metadata') and element.metadata:
            # 修复：正确处理ElementMetadata对象
            try:
                # 尝试通过getattr安全地获取属性
                font_size = getattr(element.metadata, 'font_size', None)
                if font_size is not None and font_size > 14:  # 假设标准字体大小是12
                    score += 3

                font_weight = getattr(element.metadata, 'font_weight', None)
                if font_weight == 'bold':
                    score += 2  # 粗体加分
            except (AttributeError, TypeError):
                # 如果metadata的访问方式不正确，尝试其他可能的访问方式
                try:
                    metadata_dict = element.metadata.__dict__ if hasattr(element.metadata, '__dict__') else {}
                    if 'font_size' in metadata_dict and metadata_dict['font_size'] > 14:
                        score += 3
                    if 'font_weight' in metadata_dict and metadata_dict['font_weight'] == 'bold':
                        score += 2
                except Exception:
                    # 如果所有尝试都失败，忽略元数据处理
                    pass

        return score