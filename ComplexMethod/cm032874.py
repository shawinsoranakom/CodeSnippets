def add_chunk(t, pos):
        nonlocal cks, tk_nums, delimiter
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
            tk_nums.append(tnum)
        else:
            if cks[-1].find(pos) < 0:
                t += pos
            cks[-1] += t
            tk_nums[-1] += tnum