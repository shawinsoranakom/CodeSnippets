def __init__(self, page_blocks: list):
        self.page_blocks = page_blocks

        blocks = []
        self.all_spans = []

        # 对caption块进行分类，将其分类为image_caption, table_caption, chart_caption
        page_blocks = classify_caption_blocks(page_blocks)

        # 解析每个块
        for index, block_info in enumerate(page_blocks):

            block_type = block_info["type"]
            block_content = block_info.get("content", "")
            if not block_content and block_type != BlockType.CHART:
                continue

            if block_type in [
                "text",
                "title",
                "image_caption",
                "table_caption",
                "chart_caption",
                "header",
                "footer",
                "page_footnote",
            ]:
                span = parse_text_block_spans(block_content)

            elif block_type in ["image"]:
                block_type = BlockType.IMAGE_BODY
                span = {
                    "type": ContentType.IMAGE,
                    "image_base64": block_content,
                }
            elif block_type in ["table"]:
                block_type = BlockType.TABLE_BODY
                span = {
                    "type": ContentType.TABLE,
                    "html": clean_table_html(block_content),
                }
            elif block_type in ["chart"]:
                block_type = BlockType.CHART_BODY
                span = {
                    "type": ContentType.CHART,
                    "content": block_content,
                }
                if block_info.get("image_base64"):
                    span["image_base64"] = block_info["image_base64"]
            elif block_type in ["equation"]:
                block_type = BlockType.INTERLINE_EQUATION
                span = {
                    "type": ContentType.INTERLINE_EQUATION,
                    "content": block_content,
                }
            elif block_type in ["list"]:
                # 解析嵌套列表结构，生成与VLM一致的blocks结构
                parsed_list = parse_list_block(block_info)
                if parsed_list:
                    # 使用外层index作为列表block的index
                    parsed_list["index"] = index
                    blocks.append(parsed_list)
                continue
            elif block_type in ["index"]:
                # 解析嵌套索引结构（目录），生成与list一致的blocks结构
                parsed_index = parse_index_block(block_info)
                if parsed_index:
                    parsed_index["index"] = index
                    blocks.append(parsed_index)
                continue
            else:
                # 未知类型，跳过
                continue

            # 处理span类型并添加到all_spans
            if isinstance(span, dict):
                line = {
                    "spans": [span]
                }
            elif isinstance(span, list):
                line = {
                    "spans":span
                }
            else:
                raise ValueError(f"Unsupported span type: {type(span)}")

            block = {
                    "type": block_type,
                    "lines": [line],
                    "index": index,
            }
            anchor = block_info.get("anchor")
            if (
                isinstance(anchor, str)
                and anchor.strip()
                and block_type in [BlockType.TITLE, BlockType.TEXT, BlockType.INTERLINE_EQUATION]
            ):
                block["anchor"] = anchor.strip()
            if block_type == BlockType.TITLE:
                block["is_numbered_style"] = block_info.get("is_numbered_style", False)
                block["level"] = block_info.get("level", 1)
            blocks.append(block)

        self.image_blocks = []
        self.table_blocks = []
        self.chart_blocks = []
        self.interline_equation_blocks = []
        self.text_blocks = []
        self.title_blocks = []
        self.discarded_blocks = []
        self.list_blocks = []
        self.index_blocks = []
        for block in blocks:
            if block["type"] in [BlockType.IMAGE_BODY, BlockType.IMAGE_CAPTION, BlockType.IMAGE_FOOTNOTE]:
                self.image_blocks.append(block)
            elif block["type"] in [BlockType.TABLE_BODY, BlockType.TABLE_CAPTION, BlockType.TABLE_FOOTNOTE]:
                self.table_blocks.append(block)
            elif block["type"] in [BlockType.CHART_BODY, BlockType.CHART_CAPTION]:
                self.chart_blocks.append(block)
            elif block["type"] == BlockType.INTERLINE_EQUATION:
                self.interline_equation_blocks.append(block)
            elif block["type"] == BlockType.TEXT:
                self.text_blocks.append(block)
            elif block["type"] == BlockType.TITLE:
                self.title_blocks.append(block)
            elif block["type"] in [BlockType.REF_TEXT]:
                self.ref_text_blocks.append(block)
            elif block["type"] in [BlockType.PHONETIC]:
                self.phonetic_blocks.append(block)
            elif block["type"] in [BlockType.HEADER, BlockType.FOOTER, BlockType.PAGE_NUMBER, BlockType.ASIDE_TEXT, BlockType.PAGE_FOOTNOTE]:
                self.discarded_blocks.append(block)
            elif block["type"] == BlockType.LIST:
                self.list_blocks.append(block)
            elif block["type"] == BlockType.INDEX:
                self.index_blocks.append(block)
            else:
                continue

        self.image_blocks, not_include_image_blocks = fix_two_layer_blocks(self.image_blocks, BlockType.IMAGE)
        self.table_blocks, not_include_table_blocks = fix_two_layer_blocks(self.table_blocks, BlockType.TABLE)
        self.chart_blocks, not_include_chart_blocks = fix_two_layer_blocks(self.chart_blocks, BlockType.CHART)

        for block in not_include_image_blocks + not_include_table_blocks + not_include_chart_blocks:
            block["type"] = BlockType.TEXT
            self.text_blocks.append(block)