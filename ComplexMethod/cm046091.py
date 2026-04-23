def merge_spans_to_vertical_line(spans, threshold=0.6):
    """将纵向文本的spans合并成纵向lines（从右向左阅读）"""
    if len(spans) == 0:
        return []
    else:
        # 按照x2坐标从大到小排序（从右向左）
        spans.sort(key=lambda span: span['bbox'][2], reverse=True)

        vertical_lines = []
        current_line = [spans[0]]

        for span in spans[1:]:
            # 特殊类型元素单独成列
            if span['type'] in [
                ContentType.INTERLINE_EQUATION, ContentType.IMAGE,
                ContentType.TABLE
            ] or any(s['type'] in [
                ContentType.INTERLINE_EQUATION, ContentType.IMAGE,
                ContentType.TABLE
            ] for s in current_line):
                vertical_lines.append(current_line)
                current_line = [span]
                continue

            # 如果当前的span与当前行的最后一个span在y轴上重叠，则添加到当前行
            if _is_overlaps_x_exceeds_threshold(span['bbox'], current_line[-1]['bbox'], threshold):
                current_line.append(span)
            else:
                vertical_lines.append(current_line)
                current_line = [span]

        # 添加最后一列
        if current_line:
            vertical_lines.append(current_line)

        return vertical_lines