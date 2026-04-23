def _extract_formulas(self, elements) -> List[Formula]:
        """提取文档中的公式"""
        formulas = []
        formula_pattern = r'^\s*\((\d+)\)\s*'

        # 标记可能是标题但实际是公式的索引
        formula_title_indices = set()

        # 第一遍：识别可能被误解为标题的公式
        for i, element in enumerate(elements):
            if isinstance(element, Title):
                title_text = str(element).strip()

                # 检查是否符合数学表达式模式
                math_expr_patterns = [
                    r'^(max|min|sup|inf|lim|arg\s*max|arg\s*min)\s+[a-zA-Z\u0370-\u03FF\u0400-\u04FF θΘ]+$',
                    r'^E\s*\(',  # 期望值表达式
                    r'^∑|∏|∫|∂|∇|∆',  # 以数学符号开头
                ]

                is_math_expr = any(re.search(pattern, title_text) for pattern in math_expr_patterns)

                if is_math_expr:
                    # 判断是否是真正的标题
                    # 1. 检查后面元素的长度
                    next_is_short = False
                    for j in range(i+1, min(i+3, len(elements))):
                        if isinstance(elements[j], (Text, NarrativeText)) and len(str(elements[j])) < 50:
                            next_is_short = True
                            break

                    # 2. 检查周围是否有数学符号
                    surrounding_has_math = self._surrounding_has_math_symbols(i, elements)

                    if next_is_short or surrounding_has_math:
                        formula_title_indices.add(i)

        # 第二遍：提取所有公式，包括被误识别为标题的公式
        for i, element in enumerate(elements):
            element_text = str(element).strip()
            is_formula = False
            formula_id = ""

            # 处理被误识别为标题的公式
            if i in formula_title_indices:
                is_formula = True
                formula_id = f"Formula-{len(formulas)+1}"
            else:
                # 常规公式识别逻辑，与之前相同
                formula_match = re.match(formula_pattern, element_text)

                if formula_match:
                    formula_id = f"({formula_match.group(1)})"
                    # 移除公式编号
                    element_text = re.sub(formula_pattern, '', element_text)
                    is_formula = True

            if is_formula:
                # 检查后续元素是否需要合并（例如，如果标题是"max θ"，后面元素通常是公式的其余部分）
                merged_content = element_text
                j = i + 1
                while j < min(i+3, len(elements)):
                    next_elem = elements[j]
                    next_text = str(next_elem).strip()

                    # 如果下一个元素很短且包含数学符号，可能是公式的一部分
                    if len(next_text) < 50 and re.search(r'[+\-*/=<>≤≥≈≠∑∏∫∂√∞∝∇≡]', next_text):
                        merged_content += " " + next_text
                        j += 1
                    else:
                        break

                formulas.append(Formula(
                    id=formula_id,
                    content=merged_content,
                    position=i
                ))

        return formulas