def _walk_linear(
        self,
        body: BaseOxmlElement,
    ):
        for element in body:
            # 获取元素的标签名（去除命名空间前缀）
            tag_name = etree.QName(element).localname
            # 检查是否存在内联图像（blip元素）
            drawing_blip = self.blip_xpath_expr(element)

            # 查找所有绘图元素（用于处理DrawingML）
            drawingml_els = element.findall(
                ".//w:drawing", namespaces=DocxConverter._BLIP_NAMESPACES
            )
            if drawingml_els:
                self._handle_drawingml(drawingml_els)

            # 检查文本框内容（支持多种文本框格式）
            # 仅当该元素之前未被处理时才处理
            if element not in self.processed_textbox_elements:
                # 现代 Word 文本框
                txbx_xpath = etree.XPath(
                    ".//w:txbxContent|.//v:textbox//w:p",
                    namespaces=DocxConverter._BLIP_NAMESPACES,
                )
                textbox_elements = txbx_xpath(element)

                # 未找到现代文本框，检查替代/旧版文本框格式
                if not textbox_elements and tag_name in ["drawing", "pict"]:
                    # 额外检查 DrawingML 和 VML 格式中的文本框
                    alt_txbx_xpath = etree.XPath(
                        ".//wps:txbx//w:p|.//w10:wrap//w:p|.//a:p//a:t",
                        namespaces=DocxConverter._BLIP_NAMESPACES,
                    )
                    textbox_elements = alt_txbx_xpath(element)

                    # 检查不在标准文本框内的形状文本
                    if not textbox_elements:
                        shape_text_xpath = etree.XPath(
                            ".//a:bodyPr/ancestor::*//a:t|.//a:txBody//a:t",
                            namespaces=DocxConverter._BLIP_NAMESPACES,
                        )
                        shape_text_elements = shape_text_xpath(element)
                        if shape_text_elements:
                            # 从形状文本创建自定义文本元素
                            text_content = " ".join(
                                [t.text for t in shape_text_elements if t.text]
                            )
                            if text_content.strip():
                                logger.debug(
                                    f"Found shape text: {text_content[:50]}..."
                                )
                                self.cur_page.append(
                                    {
                                        "type": BlockType.TEXT,
                                        "content": text_content,
                                    }
                                )
                if textbox_elements:
                    self.processed_textbox_elements.append(element)
                    for tb_element in textbox_elements:
                        self.processed_textbox_elements.append(tb_element)

                    logger.debug(
                        f"Found textbox content with {len(textbox_elements)} elements"
                    )
                    self._handle_textbox_content(textbox_elements)

            if tag_name == "tbl":
                # 表格是顶层块级元素，会中断活跃列表的上下文。
                # 若不重置列表状态，后续列表项会被追加到表格之前创建的列表块中，
                # 导致表格在 cur_page 中出现在那些列表项之后，产生顺序错乱。
                if self.pre_num_id != -1:
                    self.pre_num_id = -1
                    self.pre_ilevel = -1
                    self.list_block_stack = []
                    self.list_counters = {}
                try:
                    # 处理表格元素
                    self._handle_tables(element)
                except Exception:
                    # 如果表格解析失败，记录调试信息
                    logger.debug("could not parse a table, broken docx table")
            # 检查图片元素
            elif drawing_blip:
                # 判断图片是否为锚定（浮动）图片
                is_anchored = bool(
                    element.findall(
                        ".//wp:anchor",
                        namespaces=DocxConverter._BLIP_NAMESPACES,
                    )
                )
                # 锚定图片在段落中浮动定位，段落文本应出现在图片之前
                if is_anchored and tag_name == "p":
                    self._handle_text_elements(element)
                    self._handle_pictures(drawing_blip)
                else:
                    # 处理图片元素
                    self._handle_pictures(drawing_blip)
                    # 如果是段落元素，同时处理其中的文本内容（如描述性文字）
                    if tag_name == "p":
                        self._handle_text_elements(element)
            # 检查 sdt 元素
            elif tag_name == "sdt":
                sdt_content = element.find(
                    ".//w:sdtContent", namespaces=DocxConverter._BLIP_NAMESPACES
                )
                if sdt_content is not None:
                    if self._is_toc_sdt(element):
                        # 处理目录SDT，转换为INDEX块
                        self._handle_sdt_as_index(sdt_content)
                    else:
                        # 其他SDT元素，按普通文本处理
                        paragraphs = sdt_content.findall(
                            ".//w:p", namespaces=DocxConverter._BLIP_NAMESPACES
                        )
                        for p in paragraphs:
                            self._handle_text_elements(p)
            # 检查文本段落元素
            elif tag_name == "p":
                # 处理文本元素（包括段落属性如"tcPr", "sectPr"等）
                self._handle_text_elements(element)

            # 忽略其他未知元素并记录日志
            else:
                logger.debug(f"Ignoring element in DOCX with tag: {tag_name}")