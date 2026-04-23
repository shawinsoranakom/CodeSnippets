def find_group_end(text, pos, depth):
    """查找特定深度的花括号组的结束位置"""
    current_depth = depth
    i = pos

    while i < len(text):
        if text[i] == '{' and (i == 0 or not is_escaped(text, i)):
            current_depth += 1
        elif text[i] == '}' and (i == 0 or not is_escaped(text, i)):
            current_depth -= 1
            if current_depth < depth:
                return i
        i += 1

    return -1