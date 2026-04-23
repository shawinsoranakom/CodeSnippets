def draw_layout_bbox(pdf_info, pdf_bytes, out_path, filename):
    dropped_bbox_list = []
    tables_body_list, tables_caption_list, tables_footnote_list = [], [], []
    imgs_body_list, imgs_caption_list, imgs_footnote_list = [], [], []
    codes_body_list, codes_caption_list, codes_footnote_list = [], [], []
    titles_list = []
    texts_list = []
    interline_equations_list = []
    lists_list = []
    list_items_list = []
    indexs_list = []

    for page in pdf_info:
        page_dropped_list = []
        tables_body, tables_caption, tables_footnote = [], [], []
        imgs_body, imgs_caption, imgs_footnote = [], [], []
        codes_body, codes_caption, codes_footnote = [], [], []
        titles = []
        texts = []
        interline_equations = []
        lists = []
        list_items = []
        indices = []

        for dropped_bbox in page['discarded_blocks']:
            page_dropped_list.append(dropped_bbox['bbox'])
        dropped_bbox_list.append(page_dropped_list)
        for block in page["para_blocks"]:
            bbox = block["bbox"]
            if block["type"] == BlockType.TABLE:
                for nested_block in block["blocks"]:
                    bbox = nested_block["bbox"]
                    if nested_block["type"] == BlockType.TABLE_BODY:
                        tables_body.append(bbox)
                    elif nested_block["type"] == BlockType.TABLE_CAPTION:
                        tables_caption.append(bbox)
                    elif nested_block["type"] == BlockType.TABLE_FOOTNOTE:
                        if nested_block.get(SplitFlag.CROSS_PAGE, False):
                            continue
                        tables_footnote.append(bbox)
            elif block["type"] == BlockType.IMAGE:
                for nested_block in block["blocks"]:
                    bbox = nested_block["bbox"]
                    if nested_block["type"] == BlockType.IMAGE_BODY:
                        imgs_body.append(bbox)
                    elif nested_block["type"] == BlockType.IMAGE_CAPTION:
                        imgs_caption.append(bbox)
                    elif nested_block["type"] == BlockType.IMAGE_FOOTNOTE:
                        imgs_footnote.append(bbox)
            elif block["type"] == BlockType.CODE:
                for nested_block in block["blocks"]:
                    if nested_block["type"] == BlockType.CODE_BODY:
                        bbox = nested_block["bbox"]
                        codes_body.append(bbox)
                    elif nested_block["type"] == BlockType.CODE_CAPTION:
                        bbox = nested_block["bbox"]
                        codes_caption.append(bbox)
                    elif nested_block["type"] == BlockType.CODE_FOOTNOTE:
                        bbox = nested_block["bbox"]
                        codes_footnote.append(bbox)
            elif block["type"] == BlockType.CHART:
                for nested_block in block["blocks"]:
                    if nested_block["type"] == BlockType.CHART_BODY:
                        bbox = nested_block["bbox"]
                        imgs_body.append(bbox)
                    elif nested_block["type"] == BlockType.CHART_CAPTION:
                        bbox = nested_block["bbox"]
                        imgs_caption.append(bbox)
                    elif nested_block["type"] == BlockType.CHART_FOOTNOTE:
                        bbox = nested_block["bbox"]
                        imgs_footnote.append(bbox)
            elif block["type"] == BlockType.SEAL:
                imgs_body.append(bbox)
            elif block["type"] == BlockType.TITLE:
                titles.append(bbox)
            elif block["type"] in [BlockType.TEXT, BlockType.REF_TEXT, BlockType.ABSTRACT]:
                texts.append(bbox)
            elif block["type"] == BlockType.INTERLINE_EQUATION:
                interline_equations.append(bbox)
            elif block["type"] == BlockType.LIST:
                lists.append(bbox)
                if "blocks" in block:
                    for sub_block in block["blocks"]:
                        list_items.append(sub_block["bbox"])
            elif block["type"] == BlockType.INDEX:
                indices.append(bbox)

        tables_body_list.append(tables_body)
        tables_caption_list.append(tables_caption)
        tables_footnote_list.append(tables_footnote)
        imgs_body_list.append(imgs_body)
        imgs_caption_list.append(imgs_caption)
        imgs_footnote_list.append(imgs_footnote)
        titles_list.append(titles)
        texts_list.append(texts)
        interline_equations_list.append(interline_equations)
        lists_list.append(lists)
        list_items_list.append(list_items)
        indexs_list.append(indices)
        codes_body_list.append(codes_body)
        codes_caption_list.append(codes_caption)
        codes_footnote_list.append(codes_footnote)

    layout_bbox_list = []

    for page in pdf_info:
        page_block_list = []
        for block in page["para_blocks"]:
            if block["type"] in [
                BlockType.TEXT,
                BlockType.REF_TEXT,
                BlockType.ABSTRACT,
                BlockType.TITLE,
                BlockType.INTERLINE_EQUATION,
                BlockType.LIST,
                BlockType.INDEX,
                BlockType.SEAL,
            ]:
                bbox = block["bbox"]
                page_block_list.append(bbox)
            elif block["type"] in [BlockType.IMAGE, BlockType.CHART, BlockType.CODE, BlockType.TABLE]:
                for sub_block in block["blocks"]:
                    if sub_block.get(SplitFlag.CROSS_PAGE, False):
                        continue
                    bbox = sub_block["bbox"]
                    page_block_list.append(bbox)

        layout_bbox_list.append(page_block_list)

    pdf_bytes_io = BytesIO(pdf_bytes)
    pdf_docs = PdfReader(pdf_bytes_io)
    output_pdf = PdfWriter()

    for i, page in enumerate(pdf_docs.pages):
        # 获取原始页面尺寸
        page_width, page_height = float(page.cropbox[2]), float(page.cropbox[3])
        custom_page_size = (page_width, page_height)

        packet = BytesIO()
        # 使用原始PDF的尺寸创建canvas
        c = canvas.Canvas(packet, pagesize=custom_page_size)

        c = draw_bbox_without_number(i, codes_body_list, page, c, [102, 0, 204], True)
        c = draw_bbox_without_number(i, codes_caption_list, page, c, [204, 153, 255], True)
        c = draw_bbox_without_number(i, codes_footnote_list, page, c, [229, 204, 255], True)
        c = draw_bbox_without_number(i, dropped_bbox_list, page, c, [158, 158, 158], True)
        c = draw_bbox_without_number(i, tables_body_list, page, c, [204, 204, 0], True)
        c = draw_bbox_without_number(i, tables_caption_list, page, c, [255, 255, 102], True)
        c = draw_bbox_without_number(i, tables_footnote_list, page, c, [229, 255, 204], True)
        c = draw_bbox_without_number(i, imgs_body_list, page, c, [153, 255, 51], True)
        c = draw_bbox_without_number(i, imgs_caption_list, page, c, [102, 178, 255], True)
        c = draw_bbox_without_number(i, imgs_footnote_list, page, c, [255, 178, 102], True)
        c = draw_bbox_without_number(i, titles_list, page, c, [102, 102, 255], True)
        c = draw_bbox_without_number(i, texts_list, page, c, [153, 0, 76], True)
        c = draw_bbox_without_number(i, interline_equations_list, page, c, [0, 255, 0], True)
        c = draw_bbox_without_number(i, lists_list, page, c, [40, 169, 92], True)
        c = draw_bbox_without_number(i, list_items_list, page, c, [40, 169, 92], False)
        c = draw_bbox_without_number(i, indexs_list, page, c, [40, 169, 92], True)
        c = draw_bbox_with_number(i, layout_bbox_list, page, c, [255, 0, 0], False, draw_bbox=False)

        c.save()
        packet.seek(0)
        overlay_pdf = PdfReader(packet)

        # 添加检查确保overlay_pdf.pages不为空
        if len(overlay_pdf.pages) > 0:
            new_page = PageObject(pdf=None)
            new_page.update(page)
            page = new_page
            page.merge_page(overlay_pdf.pages[0])
        else:
            # 记录日志并继续处理下一个页面
            # logger.warning(f"layout.pdf: 第{i + 1}页未能生成有效的overlay PDF")
            pass

        output_pdf.add_page(page)

    # 保存结果
    with open(f"{out_path}/{filename}", "wb") as f:
        output_pdf.write(f)