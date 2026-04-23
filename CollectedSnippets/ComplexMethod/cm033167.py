def find_overlapped(box, boxes_sorted_by_y, naive=False):
        if not boxes_sorted_by_y:
            return
        bxs = boxes_sorted_by_y
        s, e, ii = 0, len(bxs), 0
        while s < e and not naive:
            ii = (e + s) // 2
            pv = bxs[ii]
            if box["bottom"] < pv["top"]:
                e = ii
                continue
            if box["top"] > pv["bottom"]:
                s = ii + 1
                continue
            break
        while s < ii:
            if box["top"] > bxs[s]["bottom"]:
                s += 1
            break
        while e - 1 > ii:
            if box["bottom"] < bxs[e - 1]["top"]:
                e -= 1
            break

        max_overlapped_i, max_overlapped = None, 0
        for i in range(s, e):
            ov = Recognizer.overlapped_area(bxs[i], box)
            if ov <= max_overlapped:
                continue
            max_overlapped_i = i
            max_overlapped = ov

        return max_overlapped_i