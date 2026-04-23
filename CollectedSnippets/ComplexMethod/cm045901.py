def _handle_sdt_as_index(self, sdt_content: BaseOxmlElement) -> None:
        """
        处理目录SDT内容，将其转换为层级化的INDEX块。

        两阶段处理：
        1. 收集所有段落及其层级；
        2. 检测目录类型（常规目录 vs 扁平列表），对层级进行修正后写入索引块。

        Args:
            sdt_content: w:sdtContent XML元素
        """
        paragraphs = sdt_content.findall(
            ".//w:p", namespaces=DocxConverter._BLIP_NAMESPACES
        )

        # --- 第一阶段：收集所有条目 ---
        toc_items: list[tuple[int, str, list, list, Optional[str]]] = []
        for p in paragraphs:
            try:
                p_obj = Paragraph(p, self.docx_obj)
                paragraph_elements = self._get_paragraph_elements(p_obj)
                text, equations = self._handle_equations_in_text(
                    element=p, text=p_obj.text
                )
                target_anchor = self._extract_toc_target_anchor(p)
                if target_anchor and target_anchor.startswith("_Toc"):
                    self.toc_anchor_set.add(target_anchor)
                if text is None:
                    continue
                text = text.strip()
                if not text:
                    continue

                toc_level = self._get_toc_item_level(p_obj)
                if toc_level is None:
                    toc_level = 0

                toc_items.append(
                    (toc_level, text, paragraph_elements, equations, target_anchor)
                )
            except Exception as e:
                logger.debug(f"Error collecting TOC paragraph: {e}")
                continue

        # --- 第二阶段：修正层级并写入索引块 ---
        is_flat = self._is_flat_list_toc(toc_items)

        # 重置索引状态，开始新的目录块
        self.index_block_stack = []
        self.pre_index_ilevel = -1

        for toc_level, text, elements, equations, target_anchor in toc_items:
            if is_flat:
                # 插图/列表清单：强制全部扁平（层级 0）
                corrected_level = 0
            else:
                # 常规目录：依据文本编号深度修正层级，解决 docx 跳级问题
                corrected_level = self._correct_toc_level_by_text(toc_level, text)

            self._add_index_item(
                ilevel=corrected_level,
                elements=elements,
                text=text,
                equations=equations,
                anchor=target_anchor,
            )

        # 处理完成后重置索引状态
        self.index_block_stack = []
        self.pre_index_ilevel = -1