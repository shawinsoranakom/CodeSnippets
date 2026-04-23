def chunk(filename, binary=None, from_page=0, to_page=100000, lang="Chinese", callback=None, parser_config=None, **kwargs):
    """
    The supported file formats are pdf, ppt, pptx.
    Every page will be treated as a chunk. And the thumbnail of every page will be stored.
    PPT file will be parsed by using this method automatically, setting-up for every PPT file is not necessary.
    """
    if parser_config is None:
        parser_config = {}
    eng = lang.lower() == "english"
    doc = {"docnm_kwd": filename, "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", filename))}
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])
    res = []
    if re.search(r"\.pptx?$", filename, re.IGNORECASE):
        try:
            ppt_parser = RAGFlowPptParser()
            for pn, txt in enumerate(ppt_parser(filename if not binary else binary, from_page, 1000000, callback)):
                d = copy.deepcopy(doc)
                pn += from_page
                d["doc_type_kwd"] = "image"
                d["page_num_int"] = [pn + 1]
                d["top_int"] = [0]
                d["position_int"] = [(pn + 1, 0, 0, 0, 0)]
                tokenize(d, txt, eng)
                res.append(d)
            return res
        except Exception as e:
            logging.warning(f"python-pptx parsing failed for {filename}: {e}, trying tika as fallback")
            if callback:
                callback(0.1, "python-pptx failed, trying tika as fallback")

            try:
                from tika import parser as tika_parser
            except Exception as tika_error:
                error_msg = f"tika not available: {tika_error}. Unsupported .ppt/.pptx parsing."
                if callback:
                    callback(0.8, error_msg)
                logging.warning(f"{error_msg} for {filename}.")
                raise NotImplementedError(error_msg)

            if binary:
                binary_data = binary
            else:
                with open(filename, 'rb') as f:
                    binary_data = f.read()
            doc_parsed = tika_parser.from_buffer(BytesIO(binary_data))

            if doc_parsed.get("content", None) is not None:
                sections = doc_parsed["content"].split("\n")
                sections = [s for s in sections if s.strip()]

                for pn, txt in enumerate(sections):
                    d = copy.deepcopy(doc)
                    pn += from_page
                    d["doc_type_kwd"] = "text"
                    d["page_num_int"] = [pn + 1]
                    d["top_int"] = [0]
                    d["position_int"] = [(pn + 1, 0, 0, 0, 0)]
                    tokenize(d, txt, eng)
                    res.append(d)

                if callback:
                    callback(0.8, "Finish parsing with tika.")
                return res
            else:
                error_msg = f"tika.parser got empty content from {filename}."
                if callback:
                    callback(0.8, error_msg)
                logging.warning(error_msg)
                raise NotImplementedError(error_msg)
    elif re.search(r"\.pdf$", filename, re.IGNORECASE):
        layout_recognizer, parser_model_name = normalize_layout_recognizer(parser_config.get("layout_recognize", "DeepDOC"))

        if isinstance(layout_recognizer, bool):
            layout_recognizer = "DeepDOC" if layout_recognizer else "Plain Text"

        name = layout_recognizer.strip().lower()
        parser = PARSERS.get(name, by_plaintext)
        callback(0.1, "Start to parse.")

        sections, _, _ = parser(
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
            **kwargs,
        )

        if not sections:
            return []

        if name in ["tcadp", "docling", "mineru", "paddleocr"]:
            parser_config["chunk_token_num"] = 0

        callback(0.8, "Finish parsing.")

        for pn, (txt, img) in enumerate(sections):
            d = copy.deepcopy(doc)
            pn += from_page
            if not is_image_like(img):
                img = None
            else:
                img = ensure_pil_image(img)
            d["image"] = img
            d["page_num_int"] = [pn + 1]
            d["top_int"] = [0]
            d["position_int"] = [(pn + 1, 0, img.size[0] if img else 0, 0, img.size[1] if img else 0)]
            tokenize(d, txt, eng)
            res.append(d)
        return res

    raise NotImplementedError("file type not supported yet(ppt, pptx, pdf supported)")