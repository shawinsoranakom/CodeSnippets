def chunk(filename, binary=None, from_page=0, to_page=100000, lang="Chinese", callback=None, **kwargs):
    """
    Only pdf is supported.
    """
    parser_config = kwargs.get("parser_config", {"chunk_token_num": 512, "delimiter": "\n!?。；！？", "layout_recognize": "DeepDOC"})
    pdf_parser = None
    doc = {"docnm_kwd": filename}
    doc["title_tks"] = rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", doc["docnm_kwd"]))
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])
    # is it English
    eng = lang.lower() == "english"  # pdf_parser.is_english
    if re.search(r"\.pdf$", filename, re.IGNORECASE):
        layout_recognizer, parser_model_name = normalize_layout_recognizer(parser_config.get("layout_recognize", "DeepDOC"))

        if isinstance(layout_recognizer, bool):
            layout_recognizer = "DeepDOC" if layout_recognizer else "Plain Text"

        name = layout_recognizer.strip().lower()
        pdf_parser = PARSERS.get(name, by_plaintext)
        callback(0.1, "Start to parse.")

        kwargs.pop("parse_method", None)
        kwargs.pop("mineru_llm_name", None)
        sections, tbls, pdf_parser = pdf_parser(
            filename=filename,
            binary=binary,
            from_page=from_page,
            to_page=to_page,
            lang=lang,
            callback=callback,
            pdf_cls=Pdf,
            layout_recognizer=layout_recognizer,
            mineru_llm_name=parser_model_name,
            paddleocr_llm_name=parser_model_name,
            parse_method="manual",
            **kwargs,
        )

        def _normalize_section(section):
            # pad section to length 3: (txt, sec_id, poss)
            if len(section) == 1:
                section = (section[0], "", [])
            elif len(section) == 2:
                section = (section[0], "", section[1])
            elif len(section) != 3:
                raise ValueError(f"Unexpected section length: {len(section)} (value={section!r})")

            txt, layoutno, poss = section
            if isinstance(poss, str):
                poss = pdf_parser.extract_positions(poss)
                if poss:
                    first = poss[0]  # tuple: ([pn], x1, x2, y1, y2)
                    pn = first[0]
                    if isinstance(pn, list) and pn:
                        pn = pn[0]  # [pn] -> pn
                        poss[0] = (pn, *first[1:])

            return (txt, layoutno, poss)

        sections = [_normalize_section(sec) for sec in sections]

        if not sections and not tbls:
            return []

        if name in ["tcadp", "docling", "mineru", "paddleocr"]:
            parser_config["chunk_token_num"] = 0

        callback(0.8, "Finish parsing.")
        outlines = extract_pdf_outlines(binary if binary is not None else filename)

        if len(sections) > 0 and len(outlines) / len(sections) > 0.03:
            max_lvl = max([lvl for _, lvl, _ in outlines])
            most_level = max(0, max_lvl - 1)
            levels = []
            for txt, _, _ in sections:
                for t, lvl, _ in outlines:
                    tks = set([t[i] + t[i + 1] for i in range(len(t) - 1)])
                    tks_ = set([txt[i] + txt[i + 1] for i in range(min(len(t), len(txt) - 1))])
                    if len(set(tks & tks_)) / max([len(tks), len(tks_), 1]) > 0.8:
                        levels.append(lvl)
                        break
                else:
                    levels.append(max_lvl + 1)

        else:
            bull = bullets_category([txt for txt, _, _ in sections])
            most_level, levels = title_frequency(bull, [(txt, lvl) for txt, lvl, _ in sections])

        assert len(sections) == len(levels)
        sec_ids = []
        sid = 0
        for i, lvl in enumerate(levels):
            if lvl <= most_level and i > 0 and lvl != levels[i - 1]:
                sid += 1
            sec_ids.append(sid)

        sections = [(txt, sec_ids[i], poss) for i, (txt, _, poss) in enumerate(sections)]
        for (img, rows), poss in tbls:
            if not rows:
                continue
            sections.append((rows if isinstance(rows, str) else rows[0], -1, [(p[0] + 1 - from_page, p[1], p[2], p[3], p[4]) for p in poss]))

        def tag(pn, left, right, top, bottom):
            if pn + left + right + top + bottom == 0:
                return ""
            return "@@{}\t{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}##".format(pn, left, right, top, bottom)

        chunks = []
        last_sid = -2
        tk_cnt = 0
        for txt, sec_id, poss in sorted(sections, key=lambda x: (x[-1][0][0], x[-1][0][3], x[-1][0][1])):
            poss = "\t".join([tag(*pos) for pos in poss])
            if tk_cnt < 32 or (tk_cnt < 1024 and (sec_id == last_sid or sec_id == -1)):
                if chunks:
                    chunks[-1] += "\n" + txt + poss
                    tk_cnt += num_tokens_from_string(txt)
                    continue
            chunks.append(txt + poss)
            tk_cnt = num_tokens_from_string(txt)
            if sec_id > -1:
                last_sid = sec_id
        tbls = vision_figure_parser_pdf_wrapper(
            tbls=tbls,
            sections=sections,
            callback=callback,
            **kwargs,
        )
        res = tokenize_table(tbls, doc, eng)
        res.extend(tokenize_chunks(chunks, doc, eng, pdf_parser))
        table_ctx = max(0, int(parser_config.get("table_context_size", 0) or 0))
        image_ctx = max(0, int(parser_config.get("image_context_size", 0) or 0))
        if table_ctx or image_ctx:
            attach_media_context(res, table_ctx, image_ctx)
        return res

    elif re.search(r"\.docx?$", filename, re.IGNORECASE):
        docx_parser = Docx()
        ti_list, tbls = docx_parser(filename, binary, from_page=0, to_page=10000, callback=callback)
        tbls = vision_figure_parser_docx_wrapper(sections=ti_list, tbls=tbls, callback=callback, **kwargs)
        res = tokenize_table(tbls, doc, eng)
        for text, image in ti_list:
            d = copy.deepcopy(doc)
            if image:
                d["image"] = image
                d["doc_type_kwd"] = "image"
            tokenize(d, text, eng)
            res.append(d)
        table_ctx = max(0, int(parser_config.get("table_context_size", 0) or 0))
        image_ctx = max(0, int(parser_config.get("image_context_size", 0) or 0))
        if table_ctx or image_ctx:
            attach_media_context(res, table_ctx, image_ctx)
        return res
    else:
        raise NotImplementedError("file type not supported yet(pdf and docx supported)")