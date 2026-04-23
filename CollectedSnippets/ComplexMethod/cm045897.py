def _detect_heading_list_numids(self) -> set:
        """
        预扫描文档，检测用作章节标题的列表numId。

        判断依据（需同时满足两个条件）：
        1. 该numId的列表项之间穿插了非列表的正文内容（段落/表格等）；
        2. 该numId的列表项出现在**多个不同的缩进层级**（ilevel > 1种），
           即为真正的多级列表结构，而非普通的单级内容条目列表。

        这样可以避免将"多段内容条目之间穿插了小标签"的单级列表误判为标题列表。

        Returns:
            set: 应当转换为标题块的列表numId集合
        """
        heading_numids = set()
        # 收集文档元素序列：("list", numid, ilevel) 或 ("content",)
        items = []
        # 记录每个numId出现过的所有ilevel，用于判断是否为真正的多级列表
        numid_ilvels: dict[int, set] = {}

        for element in self.docx_obj.element.body:
            tag_name = etree.QName(element).localname
            if tag_name == "p":
                try:
                    paragraph = Paragraph(element, self.docx_obj)
                    p_style_id, _ = self._get_label_and_level(paragraph)
                    numid, ilevel = self._get_numId_and_ilvl(paragraph)
                    if numid == 0:
                        numid = None
                    text = self._get_paragraph_text(paragraph).strip()
                except Exception:
                    continue

                if (
                    numid is not None
                    and ilevel is not None
                    and p_style_id not in ["Title", "Heading"]
                    and text
                ):
                    items.append(("list", numid, ilevel))
                    if numid not in numid_ilvels:
                        numid_ilvels[numid] = set()
                    numid_ilvels[numid].add(ilevel)
                elif p_style_id not in ["Title", "Heading"] and text:
                    items.append(("content", None, None))
            elif tag_name == "tbl":
                items.append(("content", None, None))

        # 对每个numId，检测其列表项之间是否有正文内容穿插
        # seen_numids[numid] = True 表示该numId的最后一个列表项之后出现了正文内容
        seen_numids: dict[int, bool] = {}

        for item_type, numid, ilevel in items:
            if item_type == "list":
                if numid in seen_numids and seen_numids[numid]:
                    # 上次列表项之后出现了正文内容，满足条件1
                    heading_numids.add(numid)
                seen_numids[numid] = False  # 重置：记录该numId出现了新列表项
            elif item_type == "content":
                # 将所有已见numId标记为"之后出现了正文内容"
                for nid in seen_numids:
                    seen_numids[nid] = True

        # 条件2：只保留真正的多级列表（出现过多于1种ilevel的numId）
        # 单级列表（如只有ilevel=0的内容条目列表）即使有正文段落穿插也不应转换为标题
        heading_numids = {
            nid for nid in heading_numids
            if len(numid_ilvels.get(nid, set())) > 1
        }

        if heading_numids:
            logger.debug(
                f"Detected heading-style list numIds (will convert to title blocks): {heading_numids}"
            )

        return heading_numids