def fix_left_right_pairs(latex_formula):
    """
    检测并修复LaTeX公式中\\left和\\right不在同一组的情况

    Args:
        latex_formula (str): 输入的LaTeX公式

    Returns:
        str: 修复后的LaTeX公式
    """
    # 用于跟踪花括号嵌套层级
    brace_stack = []
    # 用于存储\left信息: (位置, 深度, 分隔符)
    left_stack = []
    # 存储需要调整的\right信息: (开始位置, 结束位置, 目标位置)
    adjustments = []

    i = 0
    while i < len(latex_formula):
        # 检查是否是转义字符
        if i > 0 and latex_formula[i - 1] == '\\':
            backslash_count = 0
            j = i - 1
            while j >= 0 and latex_formula[j] == '\\':
                backslash_count += 1
                j -= 1

            if backslash_count % 2 == 1:
                i += 1
                continue

        # 检测\left命令
        if i + 5 < len(latex_formula) and latex_formula[i:i + 5] == "\\left" and i + 5 < len(latex_formula):
            delimiter = latex_formula[i + 5]
            left_stack.append((i, len(brace_stack), delimiter))
            i += 6  # 跳过\left和分隔符
            continue

        # 检测\right命令
        elif i + 6 < len(latex_formula) and latex_formula[i:i + 6] == "\\right" and i + 6 < len(latex_formula):
            delimiter = latex_formula[i + 6]

            if left_stack:
                left_pos, left_depth, left_delim = left_stack.pop()

                # 如果\left和\right不在同一花括号深度
                if left_depth != len(brace_stack):
                    # 找到\left所在花括号组的结束位置
                    target_pos = find_group_end(latex_formula, left_pos, left_depth)
                    if target_pos != -1:
                        # 记录需要移动的\right
                        adjustments.append((i, i + 7, target_pos))

            i += 7  # 跳过\right和分隔符
            continue

        # 处理花括号
        if latex_formula[i] == '{':
            brace_stack.append(i)
        elif latex_formula[i] == '}':
            if brace_stack:
                brace_stack.pop()

        i += 1

    # 应用调整，从后向前处理以避免索引变化
    if not adjustments:
        return latex_formula

    result = list(latex_formula)
    adjustments.sort(reverse=True, key=lambda x: x[0])

    for start, end, target in adjustments:
        # 提取\right部分
        right_part = result[start:end]
        # 从原位置删除
        del result[start:end]
        # 在目标位置插入
        result.insert(target, ''.join(right_part))

    return ''.join(result)