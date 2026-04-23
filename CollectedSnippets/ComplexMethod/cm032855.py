def append_context2table_image4pdf(sections: list, tabls: list, table_context_size=0, return_context=False):
    from deepdoc.parser import PdfParser
    if table_context_size <=0:
        return [] if return_context else tabls

    page_bucket = defaultdict(list)
    for i, item in enumerate(sections):
        if isinstance(item, (tuple, list)):
            if len(item) > 2:
                txt, _sec_id, poss = item[0], item[1], item[2]
            else:
                txt = item[0] if item else ""
                poss = item[1] if len(item) > 1 else ""
        else:
            txt = item
            poss = ""
        # Normal: (text, "@@...##") from naive parser -> poss is a position tag string.
        # Manual: (text, sec_id, poss_list) -> poss is a list of (page, left, right, top, bottom).
        # Paper: (text_with_@@tag, layoutno) -> poss is layoutno; parse from txt when it contains @@ tags.
        if isinstance(poss, list):
            poss = poss
        elif isinstance(poss, str):
            if "@@" not in poss and isinstance(txt, str) and "@@" in txt:
                poss = txt
            poss = PdfParser.extract_positions(poss)
        else:
            if isinstance(txt, str) and "@@" in txt:
                poss = PdfParser.extract_positions(txt)
            else:
                poss = []
        if isinstance(txt, str) and "@@" in txt:
            txt = re.sub(r"@@[0-9-]+\t[0-9.\t]+##", "", txt).strip()
        for page, left, right, top, bottom in poss:
            if isinstance(page, list):
                page = page[0] if page else 0
            page_bucket[page].append(((left, right, top, bottom), txt))

    def upper_context(page, i):
        txt = ""
        if page not in page_bucket:
            i = -1
        while num_tokens_from_string(txt) < table_context_size:
            if i < 0:
                page -= 1
                if page < 0 or page not in page_bucket:
                    break
                i = len(page_bucket[page]) -1
            blks = page_bucket[page]
            (_, _, _, _), cnt = blks[i]
            txts = re.split(r"([。!?？；！\n]|\. )", cnt, flags=re.DOTALL)[::-1]
            for j in range(0, len(txts), 2):
                txt = (txts[j+1] if j+1<len(txts) else "") + txts[j] + txt
                if num_tokens_from_string(txt) > table_context_size:
                    break
            i -= 1
        return txt

    def lower_context(page, i):
        txt = ""
        if page not in page_bucket:
            return txt
        while num_tokens_from_string(txt) < table_context_size:
            if i >= len(page_bucket[page]):
                page += 1
                if page not in page_bucket:
                    break
                i = 0
            blks = page_bucket[page]
            (_, _, _, _), cnt = blks[i]
            txts = re.split(r"([。!?？；！\n]|\. )", cnt, flags=re.DOTALL)
            for j in range(0, len(txts), 2):
                txt += txts[j] + (txts[j+1] if j+1<len(txts) else "")
                if num_tokens_from_string(txt) > table_context_size:
                    break
            i += 1
        return txt

    res = []
    contexts = []
    for (img, tb), poss in tabls:
        page, left, right, top, bott = poss[0]
        _page, _left, _right, _top, _bott = poss[-1]
        if isinstance(tb, list):
            tb = "\n".join(tb)

        i = 0
        blks = page_bucket.get(page, [])
        _tb = tb
        while i < len(blks):
            if i + 1 >= len(blks):
                if _page > page:
                    page += 1
                    i = 0
                    blks = page_bucket.get(page, [])
                    continue
                upper = upper_context(page, i)
                lower = lower_context(page + 1, 0)
                tb = upper + tb + lower
                contexts.append((upper.strip(), lower.strip()))
                break
            (_, _, t, b), txt = blks[i]
            if b > top:
                break
            (_, _, _t, _b), _txt = blks[i+1]
            if _t < _bott:
                i += 1
                continue

            upper = upper_context(page, i)
            lower = lower_context(page, i)
            tb = upper + tb + lower
            contexts.append((upper.strip(), lower.strip()))
            break

        if _tb == tb:
            upper = upper_context(page, -1)
            lower = lower_context(page + 1, 0)
            tb = upper + tb + lower
            contexts.append((upper.strip(), lower.strip()))
        if len(contexts) < len(res) + 1:
            contexts.append(("", ""))
        res.append(((img, tb), poss))
    return contexts if return_context else res