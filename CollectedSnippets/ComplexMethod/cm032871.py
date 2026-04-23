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