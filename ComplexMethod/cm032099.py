def _is_likely_section_title(self, title_text: str, element, index: int, elements) -> bool:
        """判断标题是否可能是章节标题"""
        title_lower = title_text.lower()

        # 首先检查是否在参考文献部分
        if self._is_in_references_section(index, elements):
            # 参考文献部分的标题处理策略：
            # 1. 只有特定格式的标题才被接受
            # 2. 通常参考文献中的内容不应被识别为标题

            # 检查是否是有效的参考文献标题格式
            valid_ref_title_patterns = [
                r'^references$',
                r'^bibliography$',
                r'^参考文献$',
                r'^\d+\.\s*references$',
                r'^文献$',
                r'^引用文献$'
            ]

            is_valid_ref_title = any(re.match(pattern, title_lower) for pattern in valid_ref_title_patterns)

            # 在参考文献部分，除非是明确的子分类标题，否则都不认为是标题
            if not is_valid_ref_title:
                # 检查特定格式：常见的参考文献子类别
                ref_subcategory_patterns = [
                    r'^primary\s+sources$',
                    r'^secondary\s+sources$',
                    r'^books$',
                    r'^journals$',
                    r'^conference\s+papers$',
                    r'^web\s+sources$',
                    r'^further\s+reading$',
                    r'^monographs$'
                ]

                is_ref_subcategory = any(re.match(pattern, title_lower) for pattern in ref_subcategory_patterns)

                # 如果不是子类别标题，在参考文献部分很可能不是标题
                if not is_ref_subcategory:
                    # 检查是否包含出版物特征（会议、期刊、年份等）
                    pub_features = [
                        r'conference', r'proceedings', r'journal', r'transactions',
                        r'symposium', r'workshop', r'international', r'annual',
                        r'\d{4}', r'pp\.', r'vol\.', r'pages', r'ieee', r'acm'
                    ]

                    has_pub_features = any(re.search(pattern, title_lower) for pattern in pub_features)

                    if has_pub_features:
                        return False

                    # 检查文本长度和格式特征
                    if len(title_text) > 50 or title_text.count(' ') > 10:
                        return False

                    # 检查是否包含DOI、arXiv等标识
                    if re.search(r'doi|arxiv|http|url|issn|isbn', title_lower):
                        return False

        # 检查是否为数学表达式（例如"max θ"）- 保留现有的模式检测
        math_expr_patterns = [
            r'^(max|min|sup|inf|lim|arg\s*max|arg\s*min)\s+[a-zA-Z\u0370-\u03FF\u0400-\u04FF θΘ]+$',
            r'^E\s*\(',  # 期望值表达式开头
            r'^∑|∏|∫|∂|∇|∆',  # 以数学符号开头
            r'^\s*\([a-zA-Z0-9]\)\s*$',  # 如 (a), (1) 等单个字母/数字的标识
        ]

        # 如果匹配任何数学表达式模式，不太可能是章节标题
        for pattern in math_expr_patterns:
            if re.search(pattern, title_text):
                return False

        # 检查标题文本本身是否过短（短标题通常不是章节标题，除非是明确的关键词）
        if len(title_text) < 4 and not re.match(r'^(abstract|introduction|methods?|results?|discussion|conclusion|references)$', title_lower, re.IGNORECASE):
            return False

        # 标题中包含括号、大量符号等可能是公式
        if re.search(r'[)}]n$|[([{)\]}].*[([{)\]}]|\d+[=><≥≤]|[a-z]\s*=', title_text):
            return False

        # =================== 增强后续内容长度检查 ===================
        # 查找下一个非空元素
        next_elements = []
        total_followup_content = ""
        next_title_index = -1

        # 收集标题后的内容，直到遇到另一个标题或超过限制
        for i in range(index+1, min(index+10, len(elements))):
            if str(elements[i]).strip():
                next_elements.append(elements[i])
                if not isinstance(elements[i], Title):
                    total_followup_content += str(elements[i])
                else:
                    next_title_index = i
                    break

        # 核心检查：标题后内容长度判断
        # 1. 如果后面没有内容，这不太可能是标题
        if not next_elements:
            return False

        # 2. 如果后面第一个元素不是标题但内容很短(少于100字符)
        if next_elements and not isinstance(next_elements[0], Title):
            first_element_length = len(str(next_elements[0]))
            # 检查是否存在第二个非标题元素，如果没有或内容同样很短
            if (len(next_elements) == 1 or
                (len(next_elements) > 1 and not isinstance(next_elements[1], Title) and
                 len(str(next_elements[1])) < 50)):
                # 如果后续内容总长度小于阈值，可能不是真正的标题
                if first_element_length < 100 and len(total_followup_content) < 150:
                    # 只有常见章节标题可以例外
                    section_type = self._identify_section_type(title_text)
                    main_sections = ['abstract', 'introduction', 'method', 'result',
                                   'discussion', 'conclusion', 'references', 'acknowledgement']
                    if section_type not in main_sections:
                        # 额外检查：如果紧接着的内容包含数学符号，更可能是公式的一部分
                        if re.search(r'[+\-*/=<>≤≥≈≠∑∏∫∂√∞∝∇≡∀∃∄⊂⊃∈∉]|i\s*=|x\s*[ij]|y\s*[ij*]|\(\d+\)', str(next_elements[0])):
                            return False
                        # 检查标题文本是否包含可疑的数学符号或编号
                        if re.search(r'[(){}\[\]∑∏∫i]|^\w{1,2}$', title_text):
                            return False

                        # 最后根据总体内容长度判断
                        if len(total_followup_content) < 150:
                            return False

        # 3. 如果后面第一个元素是标题，检查级别关系
        elif next_elements and isinstance(next_elements[0], Title):
            # 获取当前和下一个标题的级别
            current_level = self._estimate_title_level(element, elements)
            next_level = self._estimate_title_level(next_elements[0], elements)

            # 如果下一个标题级别不是子标题(级别更大)，当前标题可能是有问题的
            if next_level <= current_level:
                # 检查前后是否有更多数学内容
                if self._surrounding_has_math_symbols(index, elements):
                    return False

                # 对于非主要章节标题特别严格
                section_type = self._identify_section_type(title_text)
                if section_type not in ['abstract', 'introduction', 'method', 'result', 'discussion', 'conclusion', 'references']:
                    # 检查标题文本是否匹配常见章节编号模式
                    if not re.match(r'^\d+(\.\d+)*\.\s+', title_text):
                        return False

        # 定义明确的非章节标题模式
        non_section_patterns = [
            r'received|accepted|submitted|revised|published',
            r'key\s*words|keywords',
            r'^(table|表)\s*\d+',
            r'^(figure|fig\.|图)\s*\d+',
            r'^p[- ]value',  # P值通常不是章节
            r'^(age|sex|gender|stage)(\s+|:)',  # 表格中的变量名
            r'male\s+female',  # 表格内容
            r'≤|≥',  # 表格中的比较符号
            r'^not applicable\.?$',  # "Not applicable" 文本
            r'^[t](\d+)',  # T1, T2等肿瘤分期不是章节
            r'^[nm](\d+)',  # N0, M1等肿瘤分期不是章节
        ]

        # 如果匹配任何非章节模式，返回False
        for pattern in non_section_patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return False

        # 检查是否为表格内容的更强化逻辑

        # 1. 检查前后文本模式 - 表格行通常有一定的模式

        # 检查前面的元素 - 如果前面几个元素都是Title且长度相似，可能是表格
        similar_title_count = 0
        if index > 1:
            for i in range(max(0, index-5), index):
                if isinstance(elements[i], Title):
                    prev_title_text = str(elements[i]).strip()
                    # 检查长度是否相似
                    if 0.7 <= len(prev_title_text) / len(title_text) <= 1.3:
                        similar_title_count += 1
                    # 检查格式是否相似(例如都是由空格分隔的几个词)
                    if len(prev_title_text.split()) == len(title_text.split()):
                        similar_title_count += 1

        # 检查后面的元素 - 如果后面几个元素都是Title且长度相似，可能是表格
        if index < len(elements) - 1:
            for i in range(index+1, min(index+5, len(elements))):
                if isinstance(elements[i], Title):
                    next_title_text = str(elements[i]).strip()
                    # 检查长度是否相似
                    if 0.7 <= len(next_title_text) / len(title_text) <= 1.3:
                        similar_title_count += 1
                    # 检查格式是否相似
                    if len(next_title_text.split()) == len(title_text.split()):
                        similar_title_count += 1

        # 如果周围有多个相似的Title元素，可能是表格内容
        if similar_title_count >= 4:
            return False

        # 2. 检查内容特征 - 表格行通常有特定的特征

        # 检查是否像表格数据行
        if len(title_text) < 40:  # 表格行通常不会太长
            words = title_text.split()

            # 表格可能格式: "项目 数值 数值" 或 "组别 n 百分比" 等
            if 2 <= len(words) <= 6:
                # 检查是否包含数字或百分比 - 表格行特征
                has_numbers = any(re.search(r'\d', word) for word in words)
                has_percentages = '%' in title_text

                # 检查短词占比 - 表格行通常是短词
                short_words_ratio = sum(1 for word in words if len(word) <= 5) / len(words)

                # 综合判断
                if (has_numbers or has_percentages) and short_words_ratio > 0.6:
                    # 再检查内容长度 - 表格行后通常没有长内容
                    followup_content_length = self._calculate_followup_content_length(index, elements, max_elements=3)
                    if followup_content_length < 100:
                        return False

        # 3. 检查前后内容长度

        # 计算前面内容长度
        preceding_content_length = 0
        for i in range(max(0, index-3), index):
            if isinstance(elements[i], (Text, NarrativeText)):
                preceding_content_length += len(str(elements[i]))

        # 计算后面内容长度
        followup_content_length = self._calculate_followup_content_length(index, elements)

        # 真正的章节标题前面通常是另一章节的结尾(有少量文本)或文档开始，后面有大量文本
        if preceding_content_length > 200 and followup_content_length < 150:
            # 如果前面有大量文本，后面文本很少，可能不是章节标题
            return False

        # 标题应该有足够长的后续内容(除非是参考文献等特殊章节)
        section_type = self._identify_section_type(title_text)
        main_sections = ['abstract', 'introduction', 'method', 'result',
                        'discussion', 'conclusion', 'references', 'acknowledgement']

        if section_type in ['references', 'acknowledgement']:
            return True  # 特殊章节不需要内容长度检查

        # 其他章节，根据章节类型和编号情况进行判断
        if section_type in main_sections:
            return followup_content_length >= 200  # 主要章节要求200字符以上
        elif re.match(r'^\d+(\.\d+)*\.?\s+', title_text):  # 带编号的章节
            return followup_content_length >= 150  # 编号章节要求150字符以上
        else:
            return followup_content_length >= 300