def _extract_generic_structure(self, elements) -> StructuredDocument:
        """从元素列表中提取通用文档结构

        Args:
            elements: 文档元素列表

        Returns:
            StructuredDocument: 结构化文档对象
        """
        # 创建结构化文档对象
        doc = StructuredDocument(full_text="")

        # 1. 提取文档标题
        title_candidates = []
        for i, element in enumerate(elements[:5]):  # 只检查前5个元素
            if isinstance(element, Title):
                title_text = str(element).strip()
                title_candidates.append((i, title_text))

        if title_candidates:
            # 使用第一个标题作为文档标题
            doc.title = title_candidates[0][1]

        # 2. 识别所有标题元素和内容
        title_elements = []

        # 2.1 首先识别所有标题
        for i, element in enumerate(elements):
            is_heading = False
            title_text = ""
            level = 0

            # 检查元素类型
            if isinstance(element, Title):
                is_heading = True
                title_text = str(element).strip()

                # 进一步检查是否为真正的标题
                if self._is_likely_heading(title_text, element, i, elements):
                    level = self._estimate_heading_level(title_text, element)
                else:
                    is_heading = False

            # 也检查格式像标题的普通文本
            elif isinstance(element, (Text, NarrativeText)) and i > 0:
                text = str(element).strip()
                # 检查是否匹配标题模式
                if any(re.match(pattern, text) for pattern in self.HEADING_PATTERNS):
                    # 检查长度和后续内容以确认是否为标题
                    if len(text) < 100 and self._has_sufficient_following_content(i, elements):
                        is_heading = True
                        title_text = text
                        level = self._estimate_heading_level(title_text, element)

            if is_heading:
                section_type = self._identify_section_type(title_text)
                title_elements.append((i, title_text, level, section_type))

        # 2.2 为每个标题提取内容
        sections = []

        for i, (index, title_text, level, section_type) in enumerate(title_elements):
            # 确定内容范围
            content_start = index + 1
            content_end = elements[-1]  # 默认到文档结束

            # 如果有下一个标题，内容到下一个标题开始
            if i < len(title_elements) - 1:
                content_end = title_elements[i+1][0]
            else:
                content_end = len(elements)

            # 提取内容
            content = self._extract_content_between(elements, content_start, content_end)

            # 创建章节
            section = DocumentSection(
                title=title_text,
                content=content,
                level=level,
                section_type=section_type,
                is_heading_only=False if content.strip() else True
            )

            sections.append(section)

        # 3. 如果没有识别到任何章节，创建一个默认章节
        if not sections:
            all_content = self._extract_content_between(elements, 0, len(elements))

            # 尝试从内容中提取标题
            first_line = all_content.split('\n')[0] if all_content else ""
            if first_line and len(first_line) < 100:
                doc.title = first_line
                all_content = '\n'.join(all_content.split('\n')[1:])

            default_section = DocumentSection(
                title="",
                content=all_content,
                level=0,
                section_type="content"
            )
            sections.append(default_section)

        # 4. 构建层次结构
        doc.sections = self._build_section_hierarchy(sections)

        # 5. 提取完整文本
        doc.full_text = "\n\n".join([str(element) for element in elements if isinstance(element, (Text, NarrativeText, Title, ListItem))])

        return doc