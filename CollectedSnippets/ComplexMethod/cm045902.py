def _add_header_footer(self, docx_obj: DocxDocument) -> None:
        """
        处理页眉和页脚，按照分节顺序添加到 pages 列表中，过滤掉空字符串和纯数字内容
        分为整个文档是否启用奇偶页不同和每一节是否启用首页不同两种情况，
        支持行内公式和超链接，并根据类型去重
        """
        is_odd_even_different = docx_obj.settings.odd_and_even_pages_header_footer
        for sec_idx, section in enumerate(docx_obj.sections):
            # 用于去重的集合
            added_headers = set()
            added_footers = set()

            hdrs = [section.header]
            if is_odd_even_different:
                hdrs.append(section.even_page_header)
            if section.different_first_page_header_footer:
                hdrs.append(section.first_page_header)
            for hdr in hdrs:
                # 处理每个段落，支持公式和超链接
                processed_parts = []
                for par in hdr.paragraphs:
                    content = self._process_header_footer_paragraph(par)
                    if content:
                        processed_parts.append(content)
                text = " ".join(processed_parts)
                if text != "" and not text.isdigit() and text not in added_headers:
                    added_headers.add(text)
                    try:
                        self.pages[sec_idx].append(
                            {
                                "type": BlockType.HEADER,
                                "content": text,
                            }
                        )
                    except IndexError:
                        logger.error("Section index out of range when adding header.")

            ftrs = [section.footer]
            if is_odd_even_different:
                ftrs.append(section.even_page_footer)
            if section.different_first_page_header_footer:
                ftrs.append(section.first_page_footer)
            for ftr in ftrs:
                # 处理每个段落，支持公式和超链接
                processed_parts = []
                for par in ftr.paragraphs:
                    content = self._process_header_footer_paragraph(par)
                    if content:
                        processed_parts.append(content)
                text = " ".join(processed_parts)
                if text != "" and not text.isdigit() and text not in added_footers:
                    added_footers.add(text)
                    try:
                        self.pages[sec_idx].append(
                            {
                                "type": BlockType.FOOTER,
                                "content": text,
                            }
                        )
                    except IndexError:
                        logger.error("Section index out of range when adding footer.")