def construct_table(boxes, is_english=False, html=True, **kwargs):
        cap = ""
        i = 0
        while i < len(boxes):
            if TableStructureRecognizer.is_caption(boxes[i]):
                if is_english:
                    cap += " "
                cap += boxes[i]["text"]
                boxes.pop(i)
                i -= 1
            i += 1

        if not boxes:
            return []
        for b in boxes:
            b["btype"] = TableStructureRecognizer.blockType(b)
        max_type = Counter([b["btype"] for b in boxes]).items()
        max_type = max(max_type, key=lambda x: x[1])[0] if max_type else ""
        logging.debug("MAXTYPE: " + max_type)

        rowh = [b["R_bott"] - b["R_top"] for b in boxes if "R" in b]
        rowh = np.min(rowh) if rowh else 0
        boxes = Recognizer.sort_R_firstly(boxes, rowh / 2)
        # for b in boxes:print(b)
        boxes[0]["rn"] = 0
        rows = [[boxes[0]]]
        btm = boxes[0]["bottom"]
        for b in boxes[1:]:
            b["rn"] = len(rows) - 1
            lst_r = rows[-1]
            if lst_r[-1].get("R", "") != b.get("R", "") or (b["top"] >= btm - 3 and lst_r[-1].get("R", "-1") != b.get("R", "-2")):  # new row
                btm = b["bottom"]
                b["rn"] += 1
                rows.append([b])
                continue
            btm = (btm + b["bottom"]) / 2.0
            rows[-1].append(b)

        colwm = [b["C_right"] - b["C_left"] for b in boxes if "C" in b]
        colwm = np.min(colwm) if colwm else 0
        crosspage = len(set([b["page_number"] for b in boxes])) > 1
        if crosspage:
            boxes = Recognizer.sort_X_firstly(boxes, colwm / 2)
        else:
            boxes = Recognizer.sort_C_firstly(boxes, colwm / 2)
        boxes[0]["cn"] = 0
        cols = [[boxes[0]]]
        right = boxes[0]["x1"]
        for b in boxes[1:]:
            b["cn"] = len(cols) - 1
            lst_c = cols[-1]
            if (int(b.get("C", "1")) - int(lst_c[-1].get("C", "1")) == 1 and b["page_number"] == lst_c[-1]["page_number"]) or (
                b["x0"] >= right and lst_c[-1].get("C", "-1") != b.get("C", "-2")
            ):  # new col
                right = b["x1"]
                b["cn"] += 1
                cols.append([b])
                continue
            right = (right + b["x1"]) / 2.0
            cols[-1].append(b)

        tbl = [[[] for _ in range(len(cols))] for _ in range(len(rows))]
        for b in boxes:
            tbl[b["rn"]][b["cn"]].append(b)

        if len(rows) >= 4:
            # remove single in column
            j = 0
            while j < len(tbl[0]):
                e, ii = 0, 0
                for i in range(len(tbl)):
                    if tbl[i][j]:
                        e += 1
                        ii = i
                    if e > 1:
                        break
                if e > 1:
                    j += 1
                    continue
                f = (j > 0 and tbl[ii][j - 1] and tbl[ii][j - 1][0].get("text")) or j == 0
                ff = (j + 1 < len(tbl[ii]) and tbl[ii][j + 1] and tbl[ii][j + 1][0].get("text")) or j + 1 >= len(tbl[ii])
                if f and ff:
                    j += 1
                    continue
                bx = tbl[ii][j][0]
                logging.debug("Relocate column single: " + bx["text"])
                # j column only has one value
                left, right = 100000, 100000
                if j > 0 and not f:
                    for i in range(len(tbl)):
                        if tbl[i][j - 1]:
                            left = min(left, np.min([bx["x0"] - a["x1"] for a in tbl[i][j - 1]]))
                if j + 1 < len(tbl[0]) and not ff:
                    for i in range(len(tbl)):
                        if tbl[i][j + 1]:
                            right = min(right, np.min([a["x0"] - bx["x1"] for a in tbl[i][j + 1]]))
                assert left < 100000 or right < 100000
                if left < right:
                    for jj in range(j, len(tbl[0])):
                        for i in range(len(tbl)):
                            for a in tbl[i][jj]:
                                a["cn"] -= 1
                    if tbl[ii][j - 1]:
                        tbl[ii][j - 1].extend(tbl[ii][j])
                    else:
                        tbl[ii][j - 1] = tbl[ii][j]
                    for i in range(len(tbl)):
                        tbl[i].pop(j)

                else:
                    for jj in range(j + 1, len(tbl[0])):
                        for i in range(len(tbl)):
                            for a in tbl[i][jj]:
                                a["cn"] -= 1
                    if tbl[ii][j + 1]:
                        tbl[ii][j + 1].extend(tbl[ii][j])
                    else:
                        tbl[ii][j + 1] = tbl[ii][j]
                    for i in range(len(tbl)):
                        tbl[i].pop(j)
                cols.pop(j)
        assert len(cols) == len(tbl[0]), "Column NO. miss matched: %d vs %d" % (len(cols), len(tbl[0]))

        if len(cols) >= 4:
            # remove single in row
            i = 0
            while i < len(tbl):
                e, jj = 0, 0
                for j in range(len(tbl[i])):
                    if tbl[i][j]:
                        e += 1
                        jj = j
                    if e > 1:
                        break
                if e > 1:
                    i += 1
                    continue
                f = (i > 0 and tbl[i - 1][jj] and tbl[i - 1][jj][0].get("text")) or i == 0
                ff = (i + 1 < len(tbl) and tbl[i + 1][jj] and tbl[i + 1][jj][0].get("text")) or i + 1 >= len(tbl)
                if f and ff:
                    i += 1
                    continue

                bx = tbl[i][jj][0]
                logging.debug("Relocate row single: " + bx["text"])
                # i row only has one value
                up, down = 100000, 100000
                if i > 0 and not f:
                    for j in range(len(tbl[i - 1])):
                        if tbl[i - 1][j]:
                            up = min(up, np.min([bx["top"] - a["bottom"] for a in tbl[i - 1][j]]))
                if i + 1 < len(tbl) and not ff:
                    for j in range(len(tbl[i + 1])):
                        if tbl[i + 1][j]:
                            down = min(down, np.min([a["top"] - bx["bottom"] for a in tbl[i + 1][j]]))
                assert up < 100000 or down < 100000
                if up < down:
                    for ii in range(i, len(tbl)):
                        for j in range(len(tbl[ii])):
                            for a in tbl[ii][j]:
                                a["rn"] -= 1
                    if tbl[i - 1][jj]:
                        tbl[i - 1][jj].extend(tbl[i][jj])
                    else:
                        tbl[i - 1][jj] = tbl[i][jj]
                    tbl.pop(i)

                else:
                    for ii in range(i + 1, len(tbl)):
                        for j in range(len(tbl[ii])):
                            for a in tbl[ii][j]:
                                a["rn"] -= 1
                    if tbl[i + 1][jj]:
                        tbl[i + 1][jj].extend(tbl[i][jj])
                    else:
                        tbl[i + 1][jj] = tbl[i][jj]
                    tbl.pop(i)
                rows.pop(i)

        # which rows are headers
        hdset = set([])
        for i in range(len(tbl)):
            cnt, h = 0, 0
            for j, arr in enumerate(tbl[i]):
                if not arr:
                    continue
                cnt += 1
                if max_type == "Nu" and arr[0]["btype"] == "Nu":
                    continue
                if any([a.get("H") for a in arr]) or (max_type == "Nu" and arr[0]["btype"] != "Nu"):
                    h += 1
            if h / cnt > 0.5:
                hdset.add(i)

        if html:
            return TableStructureRecognizer.__html_table(cap, hdset, TableStructureRecognizer.__cal_spans(boxes, rows, cols, tbl, True))

        return TableStructureRecognizer.__desc_table(cap, hdset, TableStructureRecognizer.__cal_spans(boxes, rows, cols, tbl, False), is_english)