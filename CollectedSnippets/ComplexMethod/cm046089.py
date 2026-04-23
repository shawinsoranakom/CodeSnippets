def chars_to_content(span):
    # 检查span中的char是否为空
    if len(span['chars']) != 0:
        # 给chars按char_idx排序
        chars = sorted(span['chars'], key=lambda x: x['char_idx'])

        # Calculate the width of each character
        char_widths = [char['bbox'][2] - char['bbox'][0] for char in chars]
        # Calculate the median width
        median_width = statistics.median(char_widths)

        parts = []
        for idx, char1 in enumerate(chars):
            char2 = chars[idx + 1] if idx + 1 < len(chars) else None

            # 如果下一个char的x0和上一个char的x1距离超过0.25个字符宽度，则需要在中间插入一个空格
            if (
                char2
                and char2['bbox'][0] - char1['bbox'][2] > median_width * 0.25
                and char1['char'] != ' '
                and char2['char'] != ' '
            ):
                parts.append(char1['char'])
                parts.append(' ')
            else:
                parts.append(char1['char'])

        content = ''.join(parts)
        content = __replace_unicode(content)
        content = __replace_ligatures(content)
        content = __replace_ligatures(content)
        span['content'] = content.strip()

    del span['chars']