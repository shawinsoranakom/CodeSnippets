def _handle_text_elements(
        self,
        element: BaseOxmlElement,
    ):
        """
        处理文本元素。

        Args:
            element: 元素对象
            doc: DoclingDocument 对象

        Returns:

        """
        is_section_end = False
        if element.find(".//w:sectPr", namespaces=DocxConverter._BLIP_NAMESPACES) is not None:
            # 如果没有text内容
            if element.text == "":
                self.cur_page = []
                self.pages.append(self.cur_page)
            else:
                # 标记本节结束，处理完文本之后再分节
                is_section_end = True
        paragraph = Paragraph(element, self.docx_obj)
        paragraph_elements = self._get_paragraph_elements(paragraph)
        paragraph_text = self._get_paragraph_text(paragraph)
        paragraph_anchor = self._extract_paragraph_bookmark(element)
        text, equations = self._handle_equations_in_text(
            element=element, text=paragraph_text
        )

        if text is None:
            return None
        text = text.strip()

        # 常见的项目符号和编号列表样式。
        # "List Bullet", "List Number", "List Paragraph"
        # 识别列表是否为编号列表
        p_style_id, p_level = self._get_label_and_level(paragraph)
        numid, ilevel = self._get_numId_and_ilvl(paragraph)

        if numid == 0:
            numid = None

        # 处理列表
        if (
            numid is not None
            and ilevel is not None
            and p_style_id not in ["Title", "Heading"]
        ):
            # 通过检查 numFmt 来确认这是否实际上是编号列表
            is_numbered = self._is_numbered_list(numid, ilevel)

            if numid in self.heading_list_numids:
                # 该列表被用作章节标题（列表项间穿插了正文内容），直接转换为title block
                # 先关闭任何活跃的普通列表
                if self.pre_num_id != -1:
                    self.pre_num_id = -1
                    self.pre_ilevel = -1
                    self.list_block_stack = []
                    self.list_counters = {}
                content_text = self._build_text_with_equations_and_hyperlinks(
                    paragraph_elements, text, equations
                )
                if content_text:
                    title_block = {
                        "type": BlockType.TITLE,
                        "level": ilevel + 1,
                        "is_numbered_style": is_numbered,
                        "content": content_text,
                    }
                    if paragraph_anchor:
                        title_block["anchor"] = paragraph_anchor
                    self.cur_page.append(title_block)
            else:
                self._add_list_item(
                    numid=numid,
                    ilevel=ilevel,
                    elements=paragraph_elements,
                    is_numbered=is_numbered,
                    text=text,
                    equations=equations,
                )
            # 列表项已处理，返回
            return None
        elif (  # 列表结束处理
            numid is None
            and self.pre_num_id != -1
            and p_style_id not in ["Title", "Heading"]
        ):  # 关闭列表
            # 重置列表状态
            self.pre_num_id = -1
            self.pre_ilevel = -1
            self.list_block_stack = []
            self.list_counters = {}

        if p_style_id in ["Title"]:
            # 构建包含公式和超链接的文本
            content_text = self._build_text_with_equations_and_hyperlinks(
                paragraph_elements, text, equations
            )
            if content_text != "":
                title_block = {
                    "type": BlockType.TITLE,
                    "level": 1,
                    "is_numbered_style": False,
                    "content": content_text,
                }
                if paragraph_anchor:
                    title_block["anchor"] = paragraph_anchor
                self.cur_page.append(title_block)

        elif "Heading" in p_style_id:
            style_element = getattr(paragraph.style, "element", None)
            if style_element is not None:
                is_numbered_style = (
                    "<w:numPr>" in style_element.xml or "<w:numPr>" in element.xml
                )
            else:
                is_numbered_style = False
            # 构建包含公式和超链接的文本
            content_text = self._build_text_with_equations_and_hyperlinks(
                paragraph_elements, text, equations
            )
            if content_text != "":
                h_block = {
                    "type": BlockType.TITLE,
                    "level": p_level if p_level is not None else 2,
                    "is_numbered_style": is_numbered_style,
                    "content": content_text,
                }
                if paragraph_anchor:
                    h_block["anchor"] = paragraph_anchor
                self.cur_page.append(h_block)

        elif len(equations) > 0:
            if (paragraph_text is None or len(paragraph_text.strip()) == 0) and len(
                text
            ) > 0:
                # 独立公式
                eq_block = {
                    "type": BlockType.EQUATION,
                    "content": text.replace("<eq>", "").replace("</eq>", ""),
                }
                self.cur_page.append(eq_block)
            else:
                # 包含行内公式的文本块，同时支持超链接
                content_text = self._build_text_with_equations_and_hyperlinks(
                    paragraph_elements, text, equations
                )
                text_with_inline_eq_block = {
                    "type": BlockType.TEXT,
                    "content": content_text,
                }
                if paragraph_anchor:
                    text_with_inline_eq_block["anchor"] = paragraph_anchor
                self.cur_page.append(text_with_inline_eq_block)
        elif p_style_id in [
            "Paragraph",
            "Normal",
            "Subtitle",
            "Author",
            "DefaultText",
            "ListParagraph",
            "ListBullet",
            "Quote",
        ]:
            # 构建包含公式和超链接的文本
            content_text = self._build_text_with_equations_and_hyperlinks(
                paragraph_elements, text, equations
            )
            if content_text != "":
                text_block = {
                    "type": BlockType.TEXT,
                    "content": content_text,
                }
                if paragraph_anchor:
                    text_block["anchor"] = paragraph_anchor
                self.cur_page.append(text_block)
        # 判断是否是 Caption
        elif self._is_caption(element):
            # 构建包含公式和超链接的文本
            content_text = self._build_text_with_equations_and_hyperlinks(
                paragraph_elements, text, equations
            )
            if content_text != "":
                caption_block = {
                    "type": BlockType.CAPTION,
                    "content": content_text,
                }
                self.cur_page.append(caption_block)
        else:
            # 文本样式名称不仅有默认值，还可能有用户自定义值
            # 因此我们将所有其他标签视为纯文本
            # 构建包含公式和超链接的文本
            content_text = self._build_text_with_equations_and_hyperlinks(
                paragraph_elements, text, equations
            )
            if content_text != "":
                text_block = {
                    "type": BlockType.TEXT,
                    "content": content_text,
                }
                if paragraph_anchor:
                    text_block["anchor"] = paragraph_anchor
                self.cur_page.append(text_block)

        if is_section_end:
            self.cur_page = []
            self.pages.append(self.cur_page)