def _extract_title_and_authors(self, elements, metadata: PaperMetadata) -> None:
        """从文档中提取标题和作者信息 - 改进版"""
        # 收集所有潜在的标题候选
        title_candidates = []
        all_text = []
        raw_text = []

        # 首先收集文档前30个元素的文本，用于辅助判断
        for i, element in enumerate(elements[:30]):
            if isinstance(element, (Text, Title, NarrativeText)):
                text = str(element).strip()
                if text:
                    all_text.append(text)
                    raw_text.append(text)

        # 打印出原始文本，用于调试
        print("原始文本前10行:")
        for i, text in enumerate(raw_text[:10]):
            print(f"{i}: {text}")

        # 1. 尝试查找连续的标题片段并合并它们
        i = 0
        while i < len(all_text) - 1:
            current = all_text[i]
            next_text = all_text[i + 1]

            # 检查是否存在标题分割情况：一行以冒号结尾，下一行像是标题的延续
            if current.endswith(':') and len(current) < 50 and len(next_text) > 5 and next_text[0].isupper():
                # 合并这两行文本
                combined_title = f"{current} {next_text}"
                # 查找合并前的文本并替换
                all_text[i] = combined_title
                all_text.pop(i + 1)
                # 给合并后的标题很高的分数
                title_candidates.append((combined_title, 15, i))
            else:
                i += 1

        # 2. 首先尝试从标题元素中查找
        for i, element in enumerate(elements[:15]):  # 只检查前15个元素
            if isinstance(element, Title):
                title_text = str(element).strip()
                # 排除常见的非标题内容
                if title_text.lower() not in ['abstract', '摘要', 'introduction', '引言']:
                    # 计算标题分数（越高越可能是真正的标题）
                    score = self._evaluate_title_candidate(title_text, i, element)
                    title_candidates.append((title_text, score, i))

        # 3. 特别处理常见的论文标题格式
        for i, text in enumerate(all_text[:15]):
            # 特别检查"KIMI K1.5:"类型的前缀标题
            if re.match(r'^[A-Z][A-Z0-9\s\.]+(\s+K\d+(\.\d+)?)?:', text):
                score = 12  # 给予很高的分数
                title_candidates.append((text, score, i))

                # 如果下一行也是全大写，很可能是标题的延续
                if i+1 < len(all_text) and all_text[i+1].isupper() and len(all_text[i+1]) > 10:
                    combined_title = f"{text} {all_text[i+1]}"
                    title_candidates.append((combined_title, 15, i))  # 给合并标题更高分数

            # 匹配全大写的标题行
            elif text.isupper() and len(text) > 10 and len(text) < 100:
                score = 10 - i * 0.5  # 越靠前越可能是标题
                title_candidates.append((text, score, i))

        # 对标题候选按分数排序并选取最佳候选
        if title_candidates:
            title_candidates.sort(key=lambda x: x[1], reverse=True)
            metadata.title = title_candidates[0][0]
            title_position = title_candidates[0][2]
            print(f"所有标题候选: {title_candidates[:3]}")
        else:
            # 如果没有找到合适的标题，使用一个备选策略
            for text in all_text[:10]:
                if text.isupper() and len(text) > 10 and len(text) < 200:  # 大写且适当长度的文本
                    metadata.title = text
                    break
            title_position = 0

        # 提取作者信息 - 改进后的作者提取逻辑
        author_candidates = []

        # 1. 特别处理"TECHNICAL REPORT OF"之后的行，通常是作者或团队
        for i, text in enumerate(all_text):
            if "TECHNICAL REPORT" in text.upper() and i+1 < len(all_text):
                team_text = all_text[i+1].strip()
                if re.search(r'\b(team|group|lab)\b', team_text, re.IGNORECASE):
                    author_candidates.append((team_text, 15))

        # 2. 查找包含Team的文本
        for text in all_text[:20]:
            if "Team" in text and len(text) < 30:
                # 这很可能是团队名
                author_candidates.append((text, 12))

        # 添加作者到元数据
        if author_candidates:
            # 按分数排序
            author_candidates.sort(key=lambda x: x[1], reverse=True)

            # 去重
            seen_authors = set()
            for author, _ in author_candidates:
                if author.lower() not in seen_authors and not author.isdigit():
                    seen_authors.add(author.lower())
                    metadata.authors.append(author)

        # 如果没有找到作者，尝试查找隶属机构信息中的团队名称
        if not metadata.authors:
            for text in all_text[:20]:
                if re.search(r'\b(team|group|lab|laboratory|研究组|团队)\b', text, re.IGNORECASE):
                    if len(text) < 50:  # 避免太长的文本
                        metadata.authors.append(text.strip())
                        break

        # 提取隶属机构信息
        for i, element in enumerate(elements[:30]):
            element_text = str(element).strip()
            if re.search(r'(university|institute|department|school|laboratory|college|center|centre|\d{5,}|^[a-zA-Z]+@|学院|大学|研究所|研究院)', element_text, re.IGNORECASE):
                # 可能是隶属机构
                if element_text not in metadata.affiliations and len(element_text) > 10:
                    metadata.affiliations.append(element_text)