def chunk(filename, binary=None, from_page=0, to_page=100000,
          lang="Chinese", callback=None, **kwargs):
    """
        Only pdf is supported.
        The abstract of the paper will be sliced as an entire chunk, and will not be sliced partly.
    """
    parser_config = kwargs.get(
        "parser_config", {
            "chunk_token_num": 512, "delimiter": "\n!?。；！？", "layout_recognize": "DeepDOC"})
    if re.search(r"\.pdf$", filename, re.IGNORECASE):
        layout_recognizer, parser_model_name = normalize_layout_recognizer(
            parser_config.get("layout_recognize", "DeepDOC")
        )

        if isinstance(layout_recognizer, bool):
            layout_recognizer = "DeepDOC" if layout_recognizer else "Plain Text"

        name = layout_recognizer.strip().lower()
        pdf_parser = PARSERS.get(name, by_plaintext)
        callback(0.1, "Start to parse.")

        if name == "deepdoc":
            pdf_parser = Pdf()
            paper = pdf_parser(filename if not binary else binary,
                               from_page=from_page, to_page=to_page, callback=callback)
            sections = paper.get("sections", [])
        else:
            kwargs.pop("parse_method", None)
            kwargs.pop("mineru_llm_name", None)
            sections, tables, pdf_parser = pdf_parser(
                filename=filename,
                binary=binary,
                from_page=from_page,
                to_page=to_page,
                lang=lang,
                callback=callback,
                pdf_cls=Pdf,
                layout_recognizer=layout_recognizer,
                mineru_llm_name=parser_model_name,
                parse_method="paper",
                **kwargs
            )

            paper = {
                "title": filename,
                "authors": " ",
                "abstract": "",
                "sections": sections,
                "tables": tables
            }

        tbls = paper["tables"]
        tbls = vision_figure_parser_pdf_wrapper(
            tbls=tbls,
            sections=sections,
            callback=callback,
            **kwargs,
        )
        paper["tables"] = tbls
    else:
        raise NotImplementedError("file type not supported yet(pdf supported)")

    doc = {"docnm_kwd": filename, "authors_tks": rag_tokenizer.tokenize(paper["authors"]),
           "title_tks": rag_tokenizer.tokenize(paper["title"] if paper["title"] else filename)}
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])
    doc["authors_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["authors_tks"])
    # is it English
    eng = lang.lower() == "english"  # pdf_parser.is_english
    logging.debug("It's English.....{}".format(eng))

    res = tokenize_table(paper["tables"], doc, eng)

    if paper["abstract"]:
        d = copy.deepcopy(doc)
        txt = pdf_parser.remove_tag(paper["abstract"])
        d["important_kwd"] = ["abstract", "总结", "概括", "summary", "summarize"]
        d["important_tks"] = " ".join(d["important_kwd"])
        d["image"], poss = pdf_parser.crop(
            paper["abstract"], need_position=True)
        add_positions(d, poss)
        tokenize(d, txt, eng)
        res.append(d)

    sorted_sections = paper["sections"]
    # set pivot using the most frequent type of title,
    # then merge between 2 pivot
    bull = bullets_category([txt for txt, _ in sorted_sections])
    most_level, levels = title_frequency(bull, sorted_sections)
    assert len(sorted_sections) == len(levels)
    sec_ids = []
    sid = 0
    for i, lvl in enumerate(levels):
        if lvl <= most_level and i > 0 and lvl != levels[i - 1]:
            sid += 1
        sec_ids.append(sid)
        logging.debug("{} {} {} {}".format(lvl, sorted_sections[i][0], most_level, sid))

    chunks = []
    last_sid = -2
    for (txt, _), sec_id in zip(sorted_sections, sec_ids):
        if sec_id == last_sid:
            if chunks:
                chunks[-1] += "\n" + txt
                continue
        chunks.append(txt)
        last_sid = sec_id
    res.extend(tokenize_chunks(chunks, doc, eng, pdf_parser))
    table_ctx = max(0, int(parser_config.get("table_context_size", 0) or 0))
    image_ctx = max(0, int(parser_config.get("image_context_size", 0) or 0))
    if table_ctx or image_ctx:
        attach_media_context(res, table_ctx, image_ctx)

    return res