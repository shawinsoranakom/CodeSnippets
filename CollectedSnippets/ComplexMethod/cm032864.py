def _build_cks(sections, delimiter):
    cks = []
    tables = []
    images = []

    # extract custom delimiters wrapped by backticks: `##`, `---`, etc.
    custom_delimiters = [m.group(1) for m in re.finditer(r"`([^`]+)`", delimiter)]
    has_custom = bool(custom_delimiters)

    if has_custom:
        # escape delimiters and build alternation pattern, longest first
        custom_pattern = "|".join(
            re.escape(t) for t in sorted(set(custom_delimiters), key=len, reverse=True)
        )
        # capture delimiters so they appear in re.split results
        pattern = r"(%s)" % custom_pattern

    seg = ""
    for text, image, table in sections:
        # normalize text: ensure string and prepend newline for continuity
        if not text:
            text = ""
        else:
            text = "\n" + str(text)

        if table:
            # table chunk
            ck_text = text + str(table)
            idx = len(cks)
            cks.append({
                "text": ck_text,
                "image": image,
                "ck_type": "table",
                "tk_nums": num_tokens_from_string(ck_text),
            })
            tables.append(idx)
            continue

        if image:
            # image chunk (text kept as-is for context)
            idx = len(cks)
            cks.append({
                "text": text,
                "image": image,
                "ck_type": "image",
                "tk_nums": num_tokens_from_string(text),
            })
            images.append(idx)
            continue

        # pure text chunk(s)
        if has_custom:
            split_sec = re.split(pattern, text)
            for sub_sec in split_sec:
                # ① empty or whitespace-only segment → flush current buffer
                if not sub_sec or not sub_sec.strip():
                    if seg and seg.strip():
                        s = seg.strip()
                        cks.append({
                            "text": s,
                            "image": None,
                            "ck_type": "text",
                            "tk_nums": num_tokens_from_string(s),
                        })
                    seg = ""
                    continue

                # ② matched custom delimiter (allow surrounding whitespace)
                if re.fullmatch(custom_pattern, sub_sec.strip()):
                    if seg and seg.strip():
                        s = seg.strip()
                        cks.append({
                            "text": s,
                            "image": None,
                            "ck_type": "text",
                            "tk_nums": num_tokens_from_string(s),
                        })
                    seg = ""
                    continue

                # ③ normal text content → accumulate
                seg += sub_sec
        else:

            if text and text.strip():
                t = text.strip()
                cks.append({
                    "text": t,
                    "image": None,
                    "ck_type": "text",
                    "tk_nums": num_tokens_from_string(t),
                })

    # final flush after loop (only when custom delimiters are used)
    if has_custom and seg and seg.strip():
        s = seg.strip()
        cks.append({
            "text": s,
            "image": None,
            "ck_type": "text",
            "tk_nums": num_tokens_from_string(s),
        })

    return cks, tables, images, has_custom