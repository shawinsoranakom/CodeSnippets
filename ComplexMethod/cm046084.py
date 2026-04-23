def draw_span_bbox(pdf_info, pdf_bytes, out_path, filename):
    text_list = []
    inline_equation_list = []
    interline_equation_list = []
    image_list = []
    table_list = []
    dropped_list = []

    def get_span_info(span):
        if span['type'] == ContentType.TEXT:
            page_text_list.append(span['bbox'])
        elif span['type'] == ContentType.INLINE_EQUATION:
            page_inline_equation_list.append(span['bbox'])
        elif span['type'] == ContentType.INTERLINE_EQUATION:
            page_interline_equation_list.append(span['bbox'])
        elif span['type'] in [ContentType.IMAGE, ContentType.CHART, ContentType.SEAL]:
            page_image_list.append(span['bbox'])
        elif span['type'] == ContentType.TABLE:
            page_table_list.append(span['bbox'])

    for page in pdf_info:
        page_text_list = []
        page_inline_equation_list = []
        page_interline_equation_list = []
        page_image_list = []
        page_table_list = []
        page_dropped_list = []


        # 构造dropped_list
        for block in page['discarded_blocks']:
            for line in block['lines']:
                for span in line['spans']:
                    page_dropped_list.append(span['bbox'])
        dropped_list.append(page_dropped_list)
        # 构造其余useful_list
        # for block in page['para_blocks']:  # span直接用分段合并前的结果就可以
        for block in page['preproc_blocks']:
            if block['type'] in [
                BlockType.TEXT,
                BlockType.TITLE,
                BlockType.INTERLINE_EQUATION,
                BlockType.LIST,
                BlockType.INDEX,
                BlockType.REF_TEXT,
                BlockType.ABSTRACT,
                BlockType.SEAL,
            ]:
                for line in block['lines']:
                    for span in line['spans']:
                        get_span_info(span)
            elif block['type'] in [BlockType.IMAGE, BlockType.TABLE, BlockType.CHART, BlockType.CODE]:
                for sub_block in block['blocks']:
                    for line in sub_block['lines']:
                        for span in line['spans']:
                            get_span_info(span)
        text_list.append(page_text_list)
        inline_equation_list.append(page_inline_equation_list)
        interline_equation_list.append(page_interline_equation_list)
        image_list.append(page_image_list)
        table_list.append(page_table_list)

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

        # 获取当前页面的数据
        draw_bbox_without_number(i, text_list, page, c,[255, 0, 0], False)
        draw_bbox_without_number(i, inline_equation_list, page, c, [0, 255, 0], False)
        draw_bbox_without_number(i, interline_equation_list, page, c, [0, 0, 255], False)
        draw_bbox_without_number(i, image_list, page, c, [255, 204, 0], False)
        draw_bbox_without_number(i, table_list, page, c, [204, 0, 255], False)
        draw_bbox_without_number(i, dropped_list, page, c, [158, 158, 158], False)

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
            # logger.warning(f"span.pdf: 第{i + 1}页未能生成有效的overlay PDF")
            pass

        output_pdf.add_page(page)

    # Save the PDF
    with open(f"{out_path}/{filename}", "wb") as f:
        output_pdf.write(f)