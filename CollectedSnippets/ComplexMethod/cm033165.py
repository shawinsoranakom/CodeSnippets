def layouts_cleanup(boxes, layouts, far=2, thr=0.7):
        def not_overlapped(a, b):
            return any([a["x1"] < b["x0"],
                        a["x0"] > b["x1"],
                        a["bottom"] < b["top"],
                        a["top"] > b["bottom"]])

        i = 0
        while i + 1 < len(layouts):
            j = i + 1
            while j < min(i + far, len(layouts)) \
                    and (layouts[i].get("type", "") != layouts[j].get("type", "")
                         or not_overlapped(layouts[i], layouts[j])):
                j += 1
            if j >= min(i + far, len(layouts)):
                i += 1
                continue
            if Recognizer.overlapped_area(layouts[i], layouts[j]) < thr \
                    and Recognizer.overlapped_area(layouts[j], layouts[i]) < thr:
                i += 1
                continue

            if layouts[i].get("score") and layouts[j].get("score"):
                if layouts[i]["score"] > layouts[j]["score"]:
                    layouts.pop(j)
                else:
                    layouts.pop(i)
                continue

            area_i, area_i_1 = 0, 0
            for b in boxes:
                if not not_overlapped(b, layouts[i]):
                    area_i += Recognizer.overlapped_area(b, layouts[i], False)
                if not not_overlapped(b, layouts[j]):
                    area_i_1 += Recognizer.overlapped_area(b, layouts[j], False)

            if area_i > area_i_1:
                layouts.pop(j)
            else:
                layouts.pop(i)

        return layouts