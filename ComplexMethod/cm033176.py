def __html_table(cap, hdset, tbl):
        # constrcut HTML
        html = "<table>"
        if cap:
            html += f"<caption>{cap}</caption>"
        for i in range(len(tbl)):
            row = "<tr>"
            txts = []
            for j, arr in enumerate(tbl[i]):
                if arr is None:
                    continue
                if not arr:
                    row += "<td></td>" if i not in hdset else "<th></th>"
                    continue
                txt = ""
                if arr:
                    h = min(np.min([c["bottom"] - c["top"] for c in arr]) / 2, 10)
                    txt = " ".join([c["text"] for c in Recognizer.sort_Y_firstly(arr, h)])
                txts.append(txt)
                sp = ""
                if arr[0].get("colspan"):
                    sp = "colspan={}".format(arr[0]["colspan"])
                if arr[0].get("rowspan"):
                    sp += " rowspan={}".format(arr[0]["rowspan"])
                if i in hdset:
                    row += f"<th {sp} >" + txt + "</th>"
                else:
                    row += f"<td {sp} >" + txt + "</td>"

            if i in hdset:
                if all([t in hdset for t in txts]):
                    continue
                for t in txts:
                    hdset.add(t)

            if row != "<tr>":
                row += "</tr>"
            else:
                row = ""
            html += "\n" + row
        html += "\n</table>"
        return html