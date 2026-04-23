def __build_page_blocks(self):
        span_type = "unknown"
        for block in self.page_blocks:
            if block["type"] in [
                BlockType.ABSTRACT,
                BlockType.CODE,
                BlockType.ASIDE_TEXT,
                BlockType.INDEX,
                BlockType.DOC_TITLE,
                BlockType.CAPTION,
                BlockType.FOOTER,
                BlockType.PAGE_FOOTNOTE,
                BlockType.FORMULA_NUMBER,
                BlockType.HEADER,
                BlockType.PAGE_NUMBER,
                BlockType.PARAGRAPH_TITLE,
                BlockType.REF_TEXT,
                BlockType.TEXT,
                BlockType.VERTICAL_TEXT,
                BlockType.FOOTNOTE,
            ]:
                span_type = ContentType.TEXT
            elif block["type"] in [BlockType.IMAGE]:
                span_type = ContentType.IMAGE
            elif block["type"] in [BlockType.TABLE]:
                span_type = ContentType.TABLE
            elif block["type"] in [BlockType.CHART]:
                span_type = ContentType.CHART
            elif block["type"] in [BlockType.INTERLINE_EQUATION]:
                span_type = ContentType.INTERLINE_EQUATION
            elif block["type"] in [BlockType.SEAL]:
                span_type = ContentType.SEAL

            if span_type in [
                ContentType.IMAGE,
                ContentType.TABLE,
                ContentType.CHART,
                ContentType.INTERLINE_EQUATION,
                ContentType.SEAL
            ]:
                span = {
                    "bbox": block["bbox"],
                    "type": span_type,
                }
                if span_type == ContentType.TABLE:
                    span["html"] = block.get("html", "")
                    block.pop("html", None)
                if span_type == ContentType.INTERLINE_EQUATION:
                    span["content"] = block.get("latex", "")
                    block.pop("latex", None)
                if span_type == ContentType.SEAL:
                    span["content"] = block.get("text")
                    block.pop("text", None)

                self.all_image_spans.append(span)
                # 构造line对象
                spans = [span]
                line = {"bbox": block["bbox"], "spans": spans}
                block["lines"] = [line]
            else:
                # span填充
                block_spans = []
                for span in self.page_text_inline_formula_spans:
                    overlap_ratio = calculate_overlap_area_in_bbox1_area_ratio(
                        span['bbox'], block["bbox"]
                    )
                    if block["type"] == BlockType.FORMULA_NUMBER:
                        # OCR 检测框通常会比公式编号框更大，使用最小框重叠比避免编号文字无法回填。
                        overlap_ratio = max(
                            overlap_ratio,
                            calculate_overlap_area_2_minbox_area_ratio(
                                span['bbox'], block["bbox"]
                            ),
                        )
                    if overlap_ratio > 0.5:
                        block_spans.append(span)
                # 从spans删除已经放入block_spans中的span
                if len(block_spans) > 0:
                    for span in block_spans:
                        self.page_text_inline_formula_spans.remove(span)

                block["spans"] = block_spans
                block = self.__fix_text_block(block)