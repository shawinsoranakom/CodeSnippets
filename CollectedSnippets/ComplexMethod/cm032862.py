def naive_merge_with_images(texts, images, chunk_token_num=128, delimiter="\n。；！？", overlapped_percent=0):
    from deepdoc.parser.pdf_parser import RAGFlowPdfParser
    if not texts or len(texts) != len(images):
        return [], []
    cks = [""]
    result_images = [None]
    tk_nums = [0]

    def add_chunk(t, image, pos=""):
        nonlocal cks, result_images, tk_nums, delimiter
        tnum = num_tokens_from_string(t)
        if not pos:
            pos = ""
        if tnum < 8:
            pos = ""
        # Ensure that the length of the merged chunk does not exceed chunk_token_num
        if cks[-1] == "" or tk_nums[-1] > chunk_token_num * (100 - overlapped_percent) / 100.:
            if cks:
                overlapped = RAGFlowPdfParser.remove_tag(cks[-1])
                t = overlapped[int(len(overlapped) * (100 - overlapped_percent) / 100.):] + t
            if t.find(pos) < 0:
                t += pos
            cks.append(t)
            result_images.append(image)
            tk_nums.append(tnum)
        else:
            if cks[-1].find(pos) < 0:
                t += pos
            cks[-1] += t
            if result_images[-1] is None:
                result_images[-1] = image
            else:
                result_images[-1] = concat_img(result_images[-1], image)
            tk_nums[-1] += tnum

    custom_delimiters = [m.group(1) for m in re.finditer(r"`([^`]+)`", delimiter)]
    has_custom = bool(custom_delimiters)
    if has_custom:
        custom_pattern = "|".join(re.escape(t) for t in sorted(set(custom_delimiters), key=len, reverse=True))
        cks, result_images, tk_nums = [], [], []
        for text, image in zip(texts, images):
            text_str = text[0] if isinstance(text, tuple) else text
            if text_str is None:
                text_str = ""
            text_pos = text[1] if isinstance(text, tuple) and len(text) > 1 else ""
            split_sec = re.split(r"(%s)" % custom_pattern, text_str)
            for sub_sec in split_sec:
                if re.fullmatch(custom_pattern, sub_sec or ""):
                    continue
                text_seg = "\n" + sub_sec
                local_pos = text_pos
                if num_tokens_from_string(text_seg) < 8:
                    local_pos = ""
                if local_pos and text_seg.find(local_pos) < 0:
                    text_seg += local_pos
                cks.append(text_seg)
                result_images.append(image)
                tk_nums.append(num_tokens_from_string(text_seg))
        return cks, result_images

    for text, image in zip(texts, images):
        # if text is tuple, unpack it
        if isinstance(text, tuple):
            text_str = text[0] if text[0] is not None else ""
            text_pos = text[1] if len(text) > 1 else ""
            add_chunk("\n" + text_str, image, text_pos)
        else:
            add_chunk("\n" + (text or ""), image)

    return cks, result_images