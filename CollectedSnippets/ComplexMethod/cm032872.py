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