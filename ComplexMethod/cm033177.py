def __desc_table(cap, hdr_rowno, tbl, is_english):
        # get text of every column in header row to become header text
        clmno = len(tbl[0])
        rowno = len(tbl)
        headers = {}
        hdrset = set()
        lst_hdr = []
        de = "的" if not is_english else " for "
        for r in sorted(list(hdr_rowno)):
            headers[r] = ["" for _ in range(clmno)]
            for i in range(clmno):
                if not tbl[r][i]:
                    continue
                txt = " ".join([a["text"].strip() for a in tbl[r][i]])
                headers[r][i] = txt
                hdrset.add(txt)
            if all([not t for t in headers[r]]):
                del headers[r]
                hdr_rowno.remove(r)
                continue
            for j in range(clmno):
                if headers[r][j]:
                    continue
                if j >= len(lst_hdr):
                    break
                headers[r][j] = lst_hdr[j]
            lst_hdr = headers[r]
        for i in range(rowno):
            if i not in hdr_rowno:
                continue
            for j in range(i + 1, rowno):
                if j not in hdr_rowno:
                    break
                for k in range(clmno):
                    if not headers[j - 1][k]:
                        continue
                    if headers[j][k].find(headers[j - 1][k]) >= 0:
                        continue
                    if len(headers[j][k]) > len(headers[j - 1][k]):
                        headers[j][k] += (de if headers[j][k] else "") + headers[j - 1][k]
                    else:
                        headers[j][k] = headers[j - 1][k] + (de if headers[j - 1][k] else "") + headers[j][k]

        logging.debug(f">>>>>>>>>>>>>>>>>{cap}：SIZE:{rowno}X{clmno} Header: {hdr_rowno}")
        row_txt = []
        for i in range(rowno):
            if i in hdr_rowno:
                continue
            rtxt = []

            def append(delimer):
                nonlocal rtxt, row_txt
                rtxt = delimer.join(rtxt)
                if row_txt and len(row_txt[-1]) + len(rtxt) < 64:
                    row_txt[-1] += "\n" + rtxt
                else:
                    row_txt.append(rtxt)

            r = 0
            if len(headers.items()):
                _arr = [(i - r, r) for r, _ in headers.items() if r < i]
                if _arr:
                    _, r = min(_arr, key=lambda x: x[0])

            if r not in headers and clmno <= 2:
                for j in range(clmno):
                    if not tbl[i][j]:
                        continue
                    txt = "".join([a["text"].strip() for a in tbl[i][j]])
                    if txt:
                        rtxt.append(txt)
                if rtxt:
                    append("：")
                continue

            for j in range(clmno):
                if not tbl[i][j]:
                    continue
                txt = "".join([a["text"].strip() for a in tbl[i][j]])
                if not txt:
                    continue
                ctt = headers[r][j] if r in headers else ""
                if ctt:
                    ctt += "："
                ctt += txt
                if ctt:
                    rtxt.append(ctt)

            if rtxt:
                row_txt.append("; ".join(rtxt))

        if cap:
            if is_english:
                from_ = " in "
            else:
                from_ = "来自"
            row_txt = [t + f"\t——{from_}“{cap}”" for t in row_txt]
        return row_txt