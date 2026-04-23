def _extract_tag(self, text: str, tag: str) -> str:
        """提取标记内容"""
        if not text:
            return ""

        # 1. 标准XML格式（处理多行和特殊字符）
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if content:
                return content

        # 2. 处理特定标签的复杂内容
        if tag == "categories":
            # 处理arXiv类别
            patterns = [
                # 标准格式：<categories>cs.CL, cs.AI, cs.LG</categories>
                r"<categories>\s*((?:(?:cs|stat|math|physics|q-bio|q-fin|nlin|astro-ph|cond-mat|gr-qc|hep-[a-z]+|math-ph|nucl-[a-z]+|quant-ph)\.[A-Z]+(?:\s*,\s*)?)+)\s*</categories>",
                # 简单列表格式：cs.CL, cs.AI, cs.LG
                r"(?:^|\s)((?:(?:cs|stat|math|physics|q-bio|q-fin|nlin|astro-ph|cond-mat|gr-qc|hep-[a-z]+|math-ph|nucl-[a-z]+|quant-ph)\.[A-Z]+(?:\s*,\s*)?)+)(?:\s|$)",
                # 单个类别格式：cs.AI
                r"(?:^|\s)((?:cs|stat|math|physics|q-bio|q-fin|nlin|astro-ph|cond-mat|gr-qc|hep-[a-z]+|math-ph|nucl-[a-z]+|quant-ph)\.[A-Z]+)(?:\s|$)"
            ]

        elif tag == "query":
            # 处理搜索查询
            patterns = [
                # 完整的查询格式：<query>complex query</query>
                r"<query>\s*((?:(?:ti|abs|au|cat):[^\n]*?|(?:AND|OR|NOT|\(|\)|\d{4}|year:\d{4}|[\"'][^\"']*[\"']|\s+))+)\s*</query>",
                # 简单的关键词列表：keyword1, keyword2
                r"(?:^|\s)((?:\"[^\"]*\"|'[^']*'|[^\s,]+)(?:\s*,\s*(?:\"[^\"]*\"|'[^']*'|[^\s,]+))*)",
                # 字段搜索格式：field:value
                r"((?:ti|abs|au|cat):\s*(?:\"[^\"]*\"|'[^']*'|[^\s]+))"
            ]

        elif tag == "fields":
            # 处理字段列表
            patterns = [
                # 标准格式：<fields>field1, field2</fields>
                r"<fields>\s*([\w\s,]+)\s*</fields>",
                # 简单列表格式：field1, field2
                r"(?:^|\s)([\w]+(?:\s*,\s*[\w]+)*)",
            ]

        elif tag == "sort_by":
            # 处理排序字段
            patterns = [
                # 标准格式：<sort_by>value</sort_by>
                r"<sort_by>\s*(relevance|date|citations|submittedDate|year)\s*</sort_by>",
                # 简单值格式：relevance
                r"(?:^|\s)(relevance|date|citations|submittedDate|year)(?:\s|$)"
            ]

        else:
            # 通用模式
            patterns = [
                f"<{tag}>\s*([\s\S]*?)\s*</{tag}>",  # 标准XML格式
                f"<{tag}>([\s\S]*?)(?:</{tag}>|$)",  # 未闭合的标签
                f"[{tag}]([\s\S]*?)[/{tag}]",  # 方括号格式
                f"{tag}:\s*(.*?)(?=\n\w|$)",  # 冒号格式
                f"<{tag}>\s*(.*?)(?=<|$)"  # 部分闭合
            ]

        # 3. 尝试所有模式
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if content:  # 确保提取的内容不为空
                    return content

        # 4. 如果所有模式都失败，返回空字符串
        return ""