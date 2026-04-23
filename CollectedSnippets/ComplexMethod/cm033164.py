def overlapped_area(a, b, ratio=True):
        tp, btm, x0, x1 = a["top"], a["bottom"], a["x0"], a["x1"]
        if b["x0"] > x1 or b["x1"] < x0:
            return 0
        if b["bottom"] < tp or b["top"] > btm:
            return 0
        x0_ = max(b["x0"], x0)
        x1_ = min(b["x1"], x1)
        assert x0_ <= x1_, "Bbox mismatch! T:{},B:{},X0:{},X1:{} ==> {}".format(
            tp, btm, x0, x1, b)
        tp_ = max(b["top"], tp)
        btm_ = min(b["bottom"], btm)
        assert tp_ <= btm_, "Bbox mismatch! T:{},B:{},X0:{},X1:{} => {}".format(
            tp, btm, x0, x1, b)
        ov = (btm_ - tp_) * (x1_ - x0_) if x1 - \
                                           x0 != 0 and btm - tp != 0 else 0
        if ov > 0 and ratio:
            ov /= (x1 - x0) * (btm - tp)
        return ov