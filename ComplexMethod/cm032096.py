def _extract_abstract_and_keywords(self, elements, metadata: PaperMetadata) -> None:
        """从文档中提取摘要和关键词"""
        abstract_found = False
        keywords_found = False
        abstract_text = []

        for i, element in enumerate(elements):
            element_text = str(element).strip().lower()

            # 寻找摘要部分
            if not abstract_found and (
                isinstance(element, Title) and
                re.search(self.SECTION_PATTERNS['abstract'], element_text, re.IGNORECASE)
            ):
                abstract_found = True
                continue

            # 如果找到摘要部分，收集内容直到遇到关键词部分或新章节
            if abstract_found and not keywords_found:
                # 检查是否遇到关键词部分或新章节
                if (
                    isinstance(element, Title) or
                    re.search(self.SECTION_PATTERNS['keywords'], element_text, re.IGNORECASE) or
                    re.match(r'\b(introduction|引言|method|方法)\b', element_text, re.IGNORECASE)
                ):
                    keywords_found = re.search(self.SECTION_PATTERNS['keywords'], element_text, re.IGNORECASE)
                    abstract_found = False  # 停止收集摘要
                else:
                    # 收集摘要文本
                    if isinstance(element, (Text, NarrativeText)) and element_text:
                        abstract_text.append(element_text)

            # 如果找到关键词部分，提取关键词
            if keywords_found and not abstract_found and not metadata.keywords:
                if isinstance(element, (Text, NarrativeText)):
                    # 清除可能的"关键词:"/"Keywords:"前缀
                    cleaned_text = re.sub(r'^\s*(关键词|keywords|key\s+words)\s*[：:]\s*', '', element_text, flags=re.IGNORECASE)

                    # 尝试按不同分隔符分割
                    for separator in [';', '；', ',', '，']:
                        if separator in cleaned_text:
                            metadata.keywords = [k.strip() for k in cleaned_text.split(separator) if k.strip()]
                            break

                    # 如果未能分割，将整个文本作为一个关键词
                    if not metadata.keywords and cleaned_text:
                        metadata.keywords = [cleaned_text]

                    keywords_found = False  # 已提取关键词，停止处理

        # 设置摘要文本
        if abstract_text:
            metadata.abstract = self.config.paragraph_separator.join(abstract_text)