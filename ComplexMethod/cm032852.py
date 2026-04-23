def doc_tokenize_chunks_with_images(chunks, doc, eng, child_delimiters_pattern=None, batch_size=10):
    res = []
    for ii, ck in enumerate(chunks):
        text = ck.get("context_above", "") + ck.get("text") + ck.get("context_below", "")
        if len(text.strip()) == 0:
            continue
        logging.debug("-- {}".format(ck))
        d = copy.deepcopy(doc)
        if ck.get("image"):
            d["image"] = ck.get("image")
        add_positions(d, [[ii] * 5])

        if ck.get("ck_type") == "text":
            if child_delimiters_pattern:
                d["mom_with_weight"] = text
                res.extend(split_with_pattern(d, child_delimiters_pattern, text, eng))
                continue
        elif ck.get("ck_type") == "image":
            d["doc_type_kwd"] = "image"
        elif ck.get("ck_type") == "table":
            d["doc_type_kwd"] = "table"
        tokenize(d, text, eng)
        res.append(d)
    return res