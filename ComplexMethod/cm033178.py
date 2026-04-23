def __cal_spans(boxes, rows, cols, tbl, html=True):
        # caculate span
        clft = [np.mean([c.get("C_left", c["x0"]) for c in cln]) for cln in cols]
        crgt = [np.mean([c.get("C_right", c["x1"]) for c in cln]) for cln in cols]
        rtop = [np.mean([c.get("R_top", c["top"]) for c in row]) for row in rows]
        rbtm = [np.mean([c.get("R_btm", c["bottom"]) for c in row]) for row in rows]
        for b in boxes:
            if "SP" not in b:
                continue
            b["colspan"] = [b["cn"]]
            b["rowspan"] = [b["rn"]]
            # col span
            for j in range(0, len(clft)):
                if j == b["cn"]:
                    continue
                if clft[j] + (crgt[j] - clft[j]) / 2 < b["H_left"]:
                    continue
                if crgt[j] - (crgt[j] - clft[j]) / 2 > b["H_right"]:
                    continue
                b["colspan"].append(j)
            # row span
            for j in range(0, len(rtop)):
                if j == b["rn"]:
                    continue
                if rtop[j] + (rbtm[j] - rtop[j]) / 2 < b["H_top"]:
                    continue
                if rbtm[j] - (rbtm[j] - rtop[j]) / 2 > b["H_bott"]:
                    continue
                b["rowspan"].append(j)

        def join(arr):
            if not arr:
                return ""
            return "".join([t["text"] for t in arr])

        # rm the spaning cells
        for i in range(len(tbl)):
            for j, arr in enumerate(tbl[i]):
                if not arr:
                    continue
                if all(["rowspan" not in a and "colspan" not in a for a in arr]):
                    continue
                rowspan, colspan = [], []
                for a in arr:
                    if isinstance(a.get("rowspan", 0), list):
                        rowspan.extend(a["rowspan"])
                    if isinstance(a.get("colspan", 0), list):
                        colspan.extend(a["colspan"])
                rowspan, colspan = set(rowspan), set(colspan)
                if len(rowspan) < 2 and len(colspan) < 2:
                    for a in arr:
                        if "rowspan" in a:
                            del a["rowspan"]
                        if "colspan" in a:
                            del a["colspan"]
                    continue
                rowspan, colspan = sorted(rowspan), sorted(colspan)
                rowspan = list(range(rowspan[0], rowspan[-1] + 1))
                colspan = list(range(colspan[0], colspan[-1] + 1))
                assert i in rowspan, rowspan
                assert j in colspan, colspan
                arr = []
                for r in rowspan:
                    for c in colspan:
                        arr_txt = join(arr)
                        if tbl[r][c] and join(tbl[r][c]) != arr_txt:
                            arr.extend(tbl[r][c])
                        tbl[r][c] = None if html else arr
                for a in arr:
                    if len(rowspan) > 1:
                        a["rowspan"] = len(rowspan)
                    elif "rowspan" in a:
                        del a["rowspan"]
                    if len(colspan) > 1:
                        a["colspan"] = len(colspan)
                    elif "colspan" in a:
                        del a["colspan"]
                tbl[rowspan[0]][colspan[0]] = arr

        return tbl