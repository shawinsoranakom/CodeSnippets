def _merge_pdfs_ng(pdf1_path, pdf2_path, output_path):
    import PyPDF2  # PyPDF2这个库有严重的内存泄露问题，把它放到子进程中运行，从而方便内存的释放
    from PyPDF2.generic import NameObject, TextStringObject, ArrayObject, FloatObject, NumberObject

    Percent = 1
    # raise RuntimeError('PyPDF2 has a serious memory leak problem, please use other tools to merge PDF files.')
    # Open the first PDF file
    with open(pdf1_path, "rb") as pdf1_file:
        pdf1_reader = PyPDF2.PdfFileReader(pdf1_file)
        # Open the second PDF file
        with open(pdf2_path, "rb") as pdf2_file:
            pdf2_reader = PyPDF2.PdfFileReader(pdf2_file)
            # Create a new PDF file to store the merged pages
            output_writer = PyPDF2.PdfFileWriter()
            # Determine the number of pages in each PDF file
            num_pages = max(pdf1_reader.numPages, pdf2_reader.numPages)
            # Merge the pages from the two PDF files
            for page_num in range(num_pages):
                # Add the page from the first PDF file
                if page_num < pdf1_reader.numPages:
                    page1 = pdf1_reader.getPage(page_num)
                else:
                    page1 = PyPDF2.PageObject.createBlankPage(pdf1_reader)
                # Add the page from the second PDF file
                if page_num < pdf2_reader.numPages:
                    page2 = pdf2_reader.getPage(page_num)
                else:
                    page2 = PyPDF2.PageObject.createBlankPage(pdf1_reader)
                # Create a new empty page with double width
                new_page = PyPDF2.PageObject.createBlankPage(
                    width=int(
                        int(page1.mediaBox.getWidth())
                        + int(page2.mediaBox.getWidth()) * Percent
                    ),
                    height=max(page1.mediaBox.getHeight(), page2.mediaBox.getHeight()),
                )
                new_page.mergeTranslatedPage(page1, 0, 0)
                new_page.mergeTranslatedPage(
                    page2,
                    int(
                        int(page1.mediaBox.getWidth())
                        - int(page2.mediaBox.getWidth()) * (1 - Percent)
                    ),
                    0,
                )
                if "/Annots" in new_page:
                    annotations = new_page["/Annots"]
                    for i, annot in enumerate(annotations):
                        annot_obj = annot.get_object()

                        # 检查注释类型是否是链接（/Link）
                        if annot_obj.get("/Subtype") == "/Link":
                            # 检查是否为内部链接跳转（/GoTo）或外部URI链接（/URI）
                            action = annot_obj.get("/A")
                            if action:

                                if "/S" in action and action["/S"] == "/GoTo":
                                    # 内部链接：跳转到文档中的某个页面
                                    dest = action.get("/D")  # 目标页或目标位置
                                    # if dest and annot.idnum in page2_annot_id:
                                    # if dest in pdf2_reader.named_destinations:
                                    if dest and page2.annotations:
                                        if annot in page2.annotations:
                                            # 获取原始文件中跳转信息，包括跳转页面
                                            destination = pdf2_reader.named_destinations[
                                                dest
                                            ]
                                            page_number = (
                                                pdf2_reader.get_destination_page_number(
                                                    destination
                                                )
                                            )
                                            # 更新跳转信息，跳转到对应的页面和，指定坐标 (100, 150)，缩放比例为 100%
                                            # “/D”:[10,'/XYZ',100,100,0]
                                            if destination.dest_array[1] == "/XYZ":
                                                annot_obj["/A"].update(
                                                    {
                                                        NameObject("/D"): ArrayObject(
                                                            [
                                                                NumberObject(page_number),
                                                                destination.dest_array[1],
                                                                FloatObject(
                                                                    destination.dest_array[
                                                                        2
                                                                    ]
                                                                    + int(
                                                                        page1.mediaBox.getWidth()
                                                                    )
                                                                ),
                                                                destination.dest_array[3],
                                                                destination.dest_array[4],
                                                            ]
                                                        )  # 确保键和值是 PdfObject
                                                    }
                                                )
                                            else:
                                                annot_obj["/A"].update(
                                                    {
                                                        NameObject("/D"): ArrayObject(
                                                            [
                                                                NumberObject(page_number),
                                                                destination.dest_array[1],
                                                            ]
                                                        )  # 确保键和值是 PdfObject
                                                    }
                                                )

                                            rect = annot_obj.get("/Rect")
                                            # 更新点击坐标
                                            rect = ArrayObject(
                                                [
                                                    FloatObject(
                                                        rect[0]
                                                        + int(page1.mediaBox.getWidth())
                                                    ),
                                                    rect[1],
                                                    FloatObject(
                                                        rect[2]
                                                        + int(page1.mediaBox.getWidth())
                                                    ),
                                                    rect[3],
                                                ]
                                            )
                                            annot_obj.update(
                                                {
                                                    NameObject(
                                                        "/Rect"
                                                    ): rect  # 确保键和值是 PdfObject
                                                }
                                            )
                                    # if dest and annot.idnum in page1_annot_id:
                                    # if dest in pdf1_reader.named_destinations:
                                    if dest and page1.annotations:
                                        if annot in page1.annotations:
                                            # 获取原始文件中跳转信息，包括跳转页面
                                            destination = pdf1_reader.named_destinations[
                                                dest
                                            ]
                                            page_number = (
                                                pdf1_reader.get_destination_page_number(
                                                    destination
                                                )
                                            )
                                            # 更新跳转信息，跳转到对应的页面和，指定坐标 (100, 150)，缩放比例为 100%
                                            # “/D”:[10,'/XYZ',100,100,0]
                                            if destination.dest_array[1] == "/XYZ":
                                                annot_obj["/A"].update(
                                                    {
                                                        NameObject("/D"): ArrayObject(
                                                            [
                                                                NumberObject(page_number),
                                                                destination.dest_array[1],
                                                                FloatObject(
                                                                    destination.dest_array[
                                                                        2
                                                                    ]
                                                                ),
                                                                destination.dest_array[3],
                                                                destination.dest_array[4],
                                                            ]
                                                        )  # 确保键和值是 PdfObject
                                                    }
                                                )
                                            else:
                                                annot_obj["/A"].update(
                                                    {
                                                        NameObject("/D"): ArrayObject(
                                                            [
                                                                NumberObject(page_number),
                                                                destination.dest_array[1],
                                                            ]
                                                        )  # 确保键和值是 PdfObject
                                                    }
                                                )

                                            rect = annot_obj.get("/Rect")
                                            rect = ArrayObject(
                                                [
                                                    FloatObject(rect[0]),
                                                    rect[1],
                                                    FloatObject(rect[2]),
                                                    rect[3],
                                                ]
                                            )
                                            annot_obj.update(
                                                {
                                                    NameObject(
                                                        "/Rect"
                                                    ): rect  # 确保键和值是 PdfObject
                                                }
                                            )

                                elif "/S" in action and action["/S"] == "/URI":
                                    # 外部链接：跳转到某个URI
                                    uri = action.get("/URI")
                output_writer.addPage(new_page)
            # Save the merged PDF file
            with open(output_path, "wb") as output_file:
                output_writer.write(output_file)