def chunk(filename, binary=None, from_page=0, to_page=100000, lang="Chinese", callback=None, **kwargs):
    """
    Supported file formats are docx, pdf, excel, txt.
    This method apply the naive ways to chunk files.
    Successive text will be sliced into pieces using 'delimiter'.
    Next, these successive pieces are merge into chunks whose token number is no more than 'Max token number'.
    """
    urls = set()
    url_res = []

    is_english = lang.lower() == "english"  # is_english(cks)
    parser_config = kwargs.get("parser_config", {"chunk_token_num": 512, "delimiter": "\n!?。；！？", "layout_recognize": "DeepDOC", "analyze_hyperlink": True})

    child_deli = (parser_config.get("children_delimiter") or "").encode("utf-8").decode("unicode_escape").encode("latin1").decode("utf-8")
    cust_child_deli = re.findall(r"`([^`]+)`", child_deli)
    child_deli = "|".join(re.sub(r"`([^`]+)`", "", child_deli))
    if cust_child_deli:
        cust_child_deli = sorted(set(cust_child_deli), key=lambda x: -len(x))
        cust_child_deli = "|".join(re.escape(t) for t in cust_child_deli if t)
        child_deli += cust_child_deli

    is_markdown = False
    table_context_size = max(0, int(parser_config.get("table_context_size", 0) or 0))
    image_context_size = max(0, int(parser_config.get("image_context_size", 0) or 0))

    doc = {"docnm_kwd": filename, "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", filename))}
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])
    res = []
    pdf_parser = None
    section_images = None

    is_root = kwargs.get("is_root", True)
    embed_res = []
    if is_root:
        # Only extract embedded files at the root call
        embeds = []
        if binary is not None:
            embeds = extract_embed_file(binary)
        else:
            raise Exception("Embedding extraction from file path is not supported.")

        # Recursively chunk each embedded file and collect results
        for embed_filename, embed_bytes in embeds:
            try:
                sub_res = chunk(embed_filename, binary=embed_bytes, lang=lang, callback=callback, is_root=False, **kwargs) or []
                embed_res.extend(sub_res)
            except Exception as e:
                error_msg = f"Failed to chunk embed {embed_filename}: {e}"
                logging.error(error_msg)
                if callback:
                    callback(0.05, error_msg)
                continue

    if re.search(r"\.docx$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        if parser_config.get("analyze_hyperlink", False) and is_root:
            urls = extract_links_from_docx(binary)
            for index, url in enumerate(urls):
                html_bytes, metadata = extract_html(url)
                if not html_bytes:
                    continue
                try:
                    sub_url_res = chunk(url, html_bytes, callback=callback, lang=lang, is_root=False, **kwargs)
                except Exception as e:
                    logging.info(f"Failed to chunk url in registered file type {url}: {e}")
                    sub_url_res = chunk(f"{index}.html", html_bytes, callback=callback, lang=lang, is_root=False, **kwargs)
                url_res.extend(sub_url_res)

        # fix "There is no item named 'word/NULL' in the archive", referring to https://github.com/python-openxml/python-docx/issues/1105#issuecomment-1298075246
        _SerializedRelationships.load_from_xml = load_from_xml_v2

        # sections = (text, image, tables)
        sections = Docx()(filename, binary)
        sections = _normalize_section_text_for_rtl_presentation_forms(sections)

        # chunks list[dict]
        # images list - index of image chunk in chunks
        chunks, images = naive_merge_docx(sections, int(parser_config.get("chunk_token_num", 128)), parser_config.get("delimiter", "\n!?。；！？"), table_context_size, image_context_size)

        vision_figure_parser_docx_wrapper_naive(chunks=chunks, idx_lst=images, callback=callback, **kwargs)

        callback(0.8, "Finish parsing.")
        st = timer()

        res.extend(doc_tokenize_chunks_with_images(chunks, doc, is_english, child_delimiters_pattern=child_deli))
        logging.info("naive_merge({}): {}".format(filename, timer() - st))
        res.extend(embed_res)
        res.extend(url_res)
        return res

    elif re.search(r"\.pdf$", filename, re.IGNORECASE):
        layout_recognizer, parser_model_name = normalize_layout_recognizer(parser_config.get("layout_recognize", "DeepDOC"))

        if parser_config.get("analyze_hyperlink", False) and is_root:
            urls = extract_links_from_pdf(binary)

        if isinstance(layout_recognizer, bool):
            layout_recognizer = "DeepDOC" if layout_recognizer else "PlainText"

        name = layout_recognizer.strip().lower()
        parser = PARSERS.get(name, by_plaintext)
        callback(0.1, "Start to parse.")

        sections, tables, pdf_parser = parser(
            filename=filename,
            binary=binary,
            from_page=from_page,
            to_page=to_page,
            lang=lang,
            callback=callback,
            layout_recognizer=layout_recognizer,
            mineru_llm_name=parser_model_name,
            paddleocr_llm_name=parser_model_name,
            **kwargs,
        )
        sections = _normalize_section_text_for_rtl_presentation_forms(sections)

        if not sections and not tables:
            return []

        if table_context_size or image_context_size:
            tables = append_context2table_image4pdf(sections, tables, image_context_size)

        if name in ["tcadp", "docling", "mineru", "paddleocr"]:
            if int(parser_config.get("chunk_token_num", 0)) <= 0:
                parser_config["chunk_token_num"] = 0

        res = tokenize_table(tables, doc, is_english)
        callback(0.8, "Finish parsing.")

    elif re.search(r"\.(csv|xlsx?)$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")

        # Check if tcadp_parser is selected for spreadsheet files
        layout_recognizer = parser_config.get("layout_recognize", "DeepDOC")
        if layout_recognizer == "TCADP Parser":
            table_result_type = parser_config.get("table_result_type", "1")
            markdown_image_response_type = parser_config.get("markdown_image_response_type", "1")
            tcadp_parser = TCADPParser(table_result_type=table_result_type, markdown_image_response_type=markdown_image_response_type)
            if not tcadp_parser.check_installation():
                callback(-1, "TCADP parser not available. Please check Tencent Cloud API configuration.")
                return res

            # Determine file type based on extension
            file_type = "XLSX" if re.search(r"\.xlsx?$", filename, re.IGNORECASE) else "CSV"

            sections, tables = tcadp_parser.parse_pdf(filepath=filename, binary=binary, callback=callback, output_dir=os.environ.get("TCADP_OUTPUT_DIR", ""), file_type=file_type)
            sections = _normalize_section_text_for_rtl_presentation_forms(sections)
            parser_config["chunk_token_num"] = 0
            res = tokenize_table(tables, doc, is_english)
            callback(0.8, "Finish parsing.")
        else:
            # Default DeepDOC parser
            excel_parser = ExcelParser()
            if parser_config.get("html4excel"):
                sections = [(_, "") for _ in excel_parser.html(binary, 12) if _]
                parser_config["chunk_token_num"] = 0
            else:
                sections = [(_, "") for _ in excel_parser(binary) if _]
            sections = _normalize_section_text_for_rtl_presentation_forms(sections)

    elif re.search(r"\.(txt|py|js|java|c|cpp|h|php|go|ts|sh|cs|kt|sql)$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        sections = TxtParser()(filename, binary, parser_config.get("chunk_token_num", 128), parser_config.get("delimiter", "\n!?;。；！？"))
        sections = _normalize_section_text_for_rtl_presentation_forms(sections)
        print("\n", "-"*150, "\n")
        print(sections)
        print("\n", "-"*150, "\n")
        callback(0.8, "Finish parsing.")

    elif re.search(r"\.(md|markdown|mdx)$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        markdown_parser = Markdown(int(parser_config.get("chunk_token_num", 128)))
        sections, tables, section_images = markdown_parser(
            filename,
            binary,
            separate_tables=False,
            delimiter=parser_config.get("delimiter", "\n!?;。；！？"),
            return_section_images=True,
        )
        sections = _normalize_section_text_for_rtl_presentation_forms(sections)

        is_markdown = True

        try:
            vision_model_config = get_tenant_default_model_by_type(kwargs["tenant_id"], LLMType.IMAGE2TEXT)
            vision_model = LLMBundle(kwargs["tenant_id"], vision_model_config)
            callback(0.2, "Visual model detected. Attempting to enhance figure extraction...")
        except Exception as e:
            logging.warning(f"Failed to detect figure extraction: {e}")
            vision_model = None

        if vision_model:
            # Process images for each section
            for idx, (section_text, _) in enumerate(sections):
                images = []
                if section_images and len(section_images) > idx and section_images[idx] is not None:
                    images.append(section_images[idx])

                if images and len(images) > 0:
                    # If multiple images found, combine them using concat_img
                    combined_image = reduce(concat_img, images) if len(images) > 1 else images[0]
                    if section_images:
                        section_images[idx] = combined_image
                    else:
                        section_images = [None] * len(sections)
                        section_images[idx] = combined_image
                    markdown_vision_parser = VisionFigureParser(vision_model=vision_model, figures_data=[((combined_image, ["markdown image"]), [(0, 0, 0, 0, 0)])], **kwargs)
                    boosted_figures = markdown_vision_parser(callback=callback)
                    sections[idx] = (section_text + "\n\n" + "\n\n".join([fig[0][1] for fig in boosted_figures]), sections[idx][1])

        else:
            logging.warning("No visual model detected. Skipping figure parsing enhancement.")

        if parser_config.get("hyperlink_urls", False) and is_root:
            for idx, (section_text, _) in enumerate(sections):
                soup = markdown_parser.md_to_html(section_text)
                hyperlink_urls = markdown_parser.get_hyperlink_urls(soup)
                urls.update(hyperlink_urls)
        res = tokenize_table(tables, doc, is_english)
        callback(0.8, "Finish parsing.")

    elif re.search(r"\.(htm|html)$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        chunk_token_num = int(parser_config.get("chunk_token_num", 128))
        sections = HtmlParser()(filename, binary, chunk_token_num)
        sections = [(_, "") for _ in sections if _]
        sections = _normalize_section_text_for_rtl_presentation_forms(sections)
        callback(0.8, "Finish parsing.")

    elif re.search(r"\.epub$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        chunk_token_num = int(parser_config.get("chunk_token_num", 128))
        sections = EpubParser()(filename, binary, chunk_token_num)
        sections = [(_, "") for _ in sections if _]
        sections = _normalize_section_text_for_rtl_presentation_forms(sections)
        callback(0.8, "Finish parsing.")

    elif re.search(r"\.(json|jsonl|ldjson)$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        chunk_token_num = int(parser_config.get("chunk_token_num", 128))
        sections = JsonParser(chunk_token_num)(binary)
        sections = [(_, "") for _ in sections if _]
        sections = _normalize_section_text_for_rtl_presentation_forms(sections)
        callback(0.8, "Finish parsing.")

    elif re.search(r"\.doc$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")

        try:
            from tika import parser as tika_parser
        except Exception as e:
            callback(0.8, f"tika not available: {e}. Unsupported .doc parsing.")
            logging.warning(f"tika not available: {e}. Unsupported .doc parsing for {filename}.")
            return []

        binary = BytesIO(binary)
        doc_parsed = tika_parser.from_buffer(binary)
        if doc_parsed.get("content", None) is not None:
            sections = doc_parsed["content"].split("\n")
            sections = [(_, "") for _ in sections if _]
            sections = _normalize_section_text_for_rtl_presentation_forms(sections)
            callback(0.8, "Finish parsing.")
        else:
            error_msg = f"tika.parser got empty content from {filename}."
            callback(0.8, error_msg)
            logging.warning(error_msg)
            return []
    else:
        raise NotImplementedError("file type not supported yet(pdf, xlsx, doc, docx, txt supported)")

    st = timer()
    overlapped_percent = normalize_overlapped_percent(parser_config.get("overlapped_percent", 0))
    if is_markdown:
        merged_chunks = []
        merged_images = []
        chunk_limit = max(0, int(parser_config.get("chunk_token_num", 128)))

        current_text = ""
        current_tokens = 0
        current_image = None

        for idx, sec in enumerate(sections):
            text = sec[0] if isinstance(sec, tuple) else sec
            sec_tokens = num_tokens_from_string(text)
            sec_image = section_images[idx] if section_images and idx < len(section_images) else None

            if current_text and current_tokens + sec_tokens > chunk_limit:
                merged_chunks.append(current_text)
                merged_images.append(current_image)
                overlap_part = ""
                if overlapped_percent > 0:
                    overlap_len = int(len(current_text) * overlapped_percent / 100)
                    if overlap_len > 0:
                        overlap_part = current_text[-overlap_len:]
                current_text = overlap_part
                current_tokens = num_tokens_from_string(current_text)
                current_image = current_image if overlap_part else None

            if current_text:
                current_text += "\n" + text
            else:
                current_text = text
            current_tokens += sec_tokens

            if sec_image:
                current_image = concat_img(current_image, sec_image) if current_image else sec_image

        if current_text:
            merged_chunks.append(current_text)
            merged_images.append(current_image)

        chunks = merged_chunks
        has_images = merged_images and any(img is not None for img in merged_images)

        if has_images:
            res.extend(tokenize_chunks_with_images(chunks, doc, is_english, merged_images, child_delimiters_pattern=child_deli))
        else:
            res.extend(tokenize_chunks(chunks, doc, is_english, pdf_parser, child_delimiters_pattern=child_deli))
    else:
        if section_images:
            if all(image is None for image in section_images):
                section_images = None

        if section_images:
            chunks, images = naive_merge_with_images(sections, section_images, int(parser_config.get("chunk_token_num", 128)), parser_config.get("delimiter", "\n!?。；！？"), overlapped_percent)
            res.extend(tokenize_chunks_with_images(chunks, doc, is_english, images, child_delimiters_pattern=child_deli))
        else:
            chunks = naive_merge(sections, int(parser_config.get("chunk_token_num", 128)), parser_config.get("delimiter", "\n!?。；！？"), overlapped_percent)

            res.extend(tokenize_chunks(chunks, doc, is_english, pdf_parser, child_delimiters_pattern=child_deli))

    if urls and parser_config.get("analyze_hyperlink", False) and is_root:
        for index, url in enumerate(urls):
            html_bytes, metadata = extract_html(url)
            if not html_bytes:
                continue
            try:
                sub_url_res = chunk(url, html_bytes, callback=callback, lang=lang, is_root=False, **kwargs)
            except Exception as e:
                logging.info(f"Failed to chunk url in registered file type {url}: {e}")
                sub_url_res = chunk(f"{index}.html", html_bytes, callback=callback, lang=lang, is_root=False, **kwargs)
            url_res.extend(sub_url_res)

    logging.info("naive_merge({}): {}".format(filename, timer() - st))

    if embed_res:
        res.extend(embed_res)
    if url_res:
        res.extend(url_res)
    # if table_context_size or image_context_size:
    #    attach_media_context(res, table_context_size, image_context_size)
    return res