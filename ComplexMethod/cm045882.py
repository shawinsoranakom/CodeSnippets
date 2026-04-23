def _split_paragraph_elements_at_eq_boundaries(
        paragraph_elements: list,
        non_eq_segments: list,
    ) -> list:
        """
        在公式边界处拆分段落元素，解决格式标注跨公式边界失效的问题。

        当 _get_paragraph_elements 处理含公式（oMath）的段落时，python-docx 的
        iter_inner_content() 不会遍历 oMath 元素。如果公式前后的文本格式相同，
        它们会被合并为单个元素，导致文本跨越 <eq> 标签两侧。
        _replace_text_outside_equations 只在单个非公式片段中搜索，无法找到跨片段的文本，
        从而导致样式替换失败。

        本方法通过将这些跨边界的合并元素重新拆分为多个片段来修复此问题，
        使每个元素都对应 text_with_equations 中唯一的非公式片段。

        Args:
            paragraph_elements: (text, format, hyperlink) 元组的列表
            non_eq_segments:     从 text_with_equations 中提取的非公式文本片段列表

        Returns:
            重新拆分后的 (text, format, hyperlink) 列表，每个元素均位于单个公式片段内
        """
        if len(non_eq_segments) <= 1:
            return paragraph_elements

        # 计算各非公式片段的累积结束位置，作为分割边界
        boundaries: set[int] = set()
        pos = 0
        for seg in non_eq_segments[:-1]:   # 最后一个片段后无需分割
            pos += len(seg)
            boundaries.add(pos)

        if not boundaries:
            return paragraph_elements

        # 验证段落元素的拼接文本与非公式片段的拼接文本一致
        concat_elem_text = "".join(text for text, _, _ in paragraph_elements)
        concat_seg_text = "".join(non_eq_segments)
        if concat_elem_text != concat_seg_text:
            # 文本不匹配时安全降级：原样返回
            return paragraph_elements

        # 在边界处分割元素
        result = []
        text_pos = 0
        for (text, fmt, hyperlink) in paragraph_elements:
            if not text:
                result.append((text, fmt, hyperlink))
                text_pos += len(text)
                continue

            elem_start = text_pos
            elem_end = elem_start + len(text)
            text_pos = elem_end

            # 找到落在该元素内部的分割点
            splits_in_elem = sorted(
                b - elem_start for b in boundaries if elem_start < b < elem_end
            )

            if not splits_in_elem:
                result.append((text, fmt, hyperlink))
            else:
                prev = 0
                for split_pos in splits_in_elem:
                    fragment = text[prev:split_pos]
                    if fragment:
                        result.append((fragment, fmt, hyperlink))
                    prev = split_pos
                fragment = text[prev:]
                if fragment:
                    result.append((fragment, fmt, hyperlink))

        return result