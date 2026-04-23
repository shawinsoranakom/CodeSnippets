def parse_text_block_spans(content: str) -> list:
    """
    解析文本类block的content，提取其中的文本、行内公式、超链接和字体样式。

    支持的标签格式：
    - <eq>...</eq>: 行内公式
    - <hyperlink><text [style="..."]>...</text><url>...</url></hyperlink>: 超链接（支持样式）
    - <text style="...">...</text>: 带字体样式的普通文本

    字体样式值（逗号分隔）：bold, italic, underline, strikethrough

    Args:
        content: 文本块的content字符串，可能包含特殊标签

    Returns:
        包含多个span的列表，每个span是一个字典，包含type和content等字段。
        带样式的文本span额外包含 style 字段（list类型）。
    """
    if not content:
        return []

    # 匹配 <text> 或 <text style="..."> 开始标签
    _text_tag_re = re.compile(r'<text(?:\s+style="([^"]*)")?>')

    spans = []
    last_end = 0
    pos = 0

    while pos < len(content):
        # 查找行内公式标签 <eq>...</eq>
        eq_start = content.find('<eq>', pos)
        # 查找超链接标签 <hyperlink>
        hyperlink_start = content.find('<hyperlink>', pos)
        # 查找带样式的文本标签 <text ...>（顶层，不在 hyperlink 内部）
        text_tag_match = _text_tag_re.search(content, pos)
        text_tag_start = text_tag_match.start() if text_tag_match else -1

        # 收集所有有效的标签位置
        candidates = []
        if eq_start != -1:
            candidates.append((eq_start, 'eq'))
        if hyperlink_start != -1:
            candidates.append((hyperlink_start, 'hyperlink'))
        if text_tag_start != -1:
            candidates.append((text_tag_start, 'text'))

        # 没有找到任何标签，处理剩余文本
        if not candidates:
            remaining_text = content[last_end:]
            if remaining_text:
                spans.append({
                    "type": ContentType.TEXT,
                    "content": remaining_text
                })
            break

        # 取位置最小的标签
        next_tag_pos, next_tag_type = min(candidates, key=lambda x: x[0])

        # 处理标签前的文本
        if next_tag_pos > last_end:
            text_before = content[last_end:next_tag_pos]
            if text_before:
                spans.append({
                    "type": ContentType.TEXT,
                    "content": text_before
                })

        # 处理行内公式
        if next_tag_type == 'eq':
            eq_end = content.find('</eq>', next_tag_pos)
            if eq_end != -1:
                formula_content = content[next_tag_pos + 4:eq_end]
                spans.append({
                    "type": ContentType.INLINE_EQUATION,
                    "content": formula_content
                })
                pos = eq_end + 5  # 跳过</eq>
                last_end = pos
            else:
                # 未找到闭合标签，将<eq>作为普通文本处理
                spans.append({
                    "type": ContentType.TEXT,
                    "content": content[last_end:]
                })
                break

        # 处理带样式的文本标签
        elif next_tag_type == 'text':
            text_end = content.find('</text>', next_tag_pos)
            if text_end != -1:
                # text_tag_match 对应当前 next_tag_pos 的匹配
                # 重新匹配确保位置对齐
                tag_open_end = content.find('>', next_tag_pos) + 1
                text_content = content[tag_open_end:text_end]
                style_str = text_tag_match.group(1) if text_tag_match and text_tag_match.start() == next_tag_pos else None
                span = {
                    "type": ContentType.TEXT,
                    "content": text_content
                }
                if style_str:
                    span["style"] = [s.strip() for s in style_str.split(',') if s.strip()]
                spans.append(span)
                pos = text_end + 7  # 跳过 </text>
                last_end = pos
            else:
                # 未找到闭合标签，作为普通文本处理
                spans.append({
                    "type": ContentType.TEXT,
                    "content": content[last_end:]
                })
                break

        # 处理超链接
        elif next_tag_type == 'hyperlink':
            hyperlink_end = content.find('</hyperlink>', next_tag_pos)
            if hyperlink_end != -1:
                # 提取超链接内容
                hyperlink_content = content[next_tag_pos + 11:hyperlink_end]

                # 解析内部的 <text [style="..."]> 和 <url> 标签
                inner_text_match = _text_tag_re.search(hyperlink_content)
                text_end_in_hl = hyperlink_content.find('</text>')
                url_start = hyperlink_content.find('<url>')
                url_end = hyperlink_content.find('</url>')

                if inner_text_match and text_end_in_hl != -1 and url_start != -1 and url_end != -1:
                    style_str = inner_text_match.group(1)
                    link_text_start = inner_text_match.end()  # 开始标签结束后的位置
                    link_text = hyperlink_content[link_text_start:text_end_in_hl]
                    link_url = hyperlink_content[url_start + 5:url_end]

                    span = {
                        "type": ContentType.HYPERLINK,
                        "content": link_text,
                        "url": link_url
                    }
                    if style_str:
                        span["style"] = [s.strip() for s in style_str.split(',') if s.strip()]
                    spans.append(span)
                    pos = hyperlink_end + 12  # 跳过</hyperlink>
                    last_end = pos
                else:
                    # 超链接格式不正确，作为普通文本处理
                    spans.append({
                        "type": ContentType.TEXT,
                        "content": content[last_end:]
                    })
                    break
            else:
                # 未找到闭合标签，将<hyperlink>作为普通文本处理
                spans.append({
                    "type": ContentType.TEXT,
                    "content": content[last_end:]
                })
                break

    return spans