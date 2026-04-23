def _is_toc_sdt(self, element: BaseOxmlElement) -> bool:
        """
        检测SDT元素是否为目录(Table of Contents)。

        检测策略：
        1. 检查 w:sdtPr 中的 docPartGallery 或 tag 元素
        2. 回退到检查内容中的段落样式是否为 "TOC N" 格式

        Args:
            element: SDT XML元素

        Returns:
            bool: 如果是目录SDT返回 True，否则返回 False
        """
        # 方法1: 检查 w:sdtPr 中的 docPartGallery
        sdt_pr = element.find("w:sdtPr", namespaces=DocxConverter._BLIP_NAMESPACES)
        if sdt_pr is not None:
            doc_part_gallery = sdt_pr.find(
                ".//w:docPartGallery", namespaces=DocxConverter._BLIP_NAMESPACES
            )
            if doc_part_gallery is not None:
                val = doc_part_gallery.get(self.XML_KEY, "")
                if "Table of Contents" in val or "toc" in val.lower():
                    return True

            # 检查 tag 元素的值
            tag_elem = sdt_pr.find("w:tag", namespaces=DocxConverter._BLIP_NAMESPACES)
            if tag_elem is not None:
                val = tag_elem.get(self.XML_KEY, "").lower().replace(" ", "")
                if "toc" in val or "contents" in val or "tableofcontents" in val:
                    return True

        # 方法2: 检查内容段落的样式是否为 "TOC N" 格式
        sdt_content = element.find(
            "w:sdtContent", namespaces=DocxConverter._BLIP_NAMESPACES
        )
        if sdt_content is not None:
            paragraphs = sdt_content.findall(
                "w:p", namespaces=DocxConverter._BLIP_NAMESPACES
            )
            for p in paragraphs[:5]:  # 只检查前5个段落即可判断
                try:
                    p_obj = Paragraph(p, self.docx_obj)
                    if p_obj.style and p_obj.style.name:
                        style_name = p_obj.style.name
                        if re.match(r'^TOC\s*\d+$', style_name, re.IGNORECASE) or \
                           re.match(r'^目录\s*\d+$', style_name):
                            return True
                except Exception:
                    continue

        return False