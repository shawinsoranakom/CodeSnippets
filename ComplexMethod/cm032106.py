def _is_in_references_section(self, index: int, elements) -> bool:
        """判断元素是否位于参考文献部分

        Args:
            index: 当前元素索引
            elements: 所有元素列表

        Returns:
            bool: 是否在参考文献部分
        """
        # 方法1：查找前面是否有明确的参考文献标题
        for i in range(index-1, max(0, index-100), -1):
            if isinstance(elements[i], Title):
                title_text = str(elements[i]).lower().strip()
                if re.search(r'^(references|bibliography|参考文献|引用|文献)(\s|$)', title_text):
                    return True
                # 检查编号形式
                if re.match(r'^\d+\.\s*(references|bibliography|参考文献)', title_text):
                    return True

        # 方法2：基于位置启发式（通常参考文献在论文末尾）
        if index > len(elements) * 0.75:  # 如果在文档后四分之一
            # 搜索前后文本是否包含参考文献特征
            ref_features = 0
            window = 20  # 查看周围20个元素

            start = max(0, index - window)
            end = min(len(elements), index + window)

            for i in range(start, end):
                if i == index:
                    continue

                text = str(elements[i]).lower()

                # 检查参考文献特征
                if re.search(r'\[\d+\]|\(\d{4}\)|et\s+al\.', text):
                    ref_features += 1
                if re.search(r'proceedings|journal|conference|transactions|vol\.|pp\.', text):
                    ref_features += 1
                if re.search(r'doi:|arxiv:|https?://|ieee|acm|springer', text):
                    ref_features += 1

            # 如果周围文本具有足够的参考文献特征
            if ref_features >= 5:
                return True

        return False