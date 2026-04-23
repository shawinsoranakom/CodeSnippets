def get_bounds_by_page(ck):
        bounds = {}
        try:
            if ck.get("position_int"):
                for pos in ck["position_int"]:
                    if not pos or len(pos) < 5:
                        continue
                    pn, _, _, top, bottom = pos
                    if pn is None or top is None:
                        continue
                    top_val = float(top)
                    bottom_val = float(bottom) if bottom is not None else top_val
                    if bottom_val < top_val:
                        top_val, bottom_val = bottom_val, top_val
                    pn = int(pn)
                    if pn in bounds:
                        bounds[pn] = (min(bounds[pn][0], top_val), max(bounds[pn][1], bottom_val))
                    else:
                        bounds[pn] = (top_val, bottom_val)
            else:
                pn = None
                if ck.get("page_num_int"):
                    pn = ck["page_num_int"][0]
                elif ck.get("page_number") is not None:
                    pn = ck.get("page_number")
                if pn is None:
                    return bounds
                top = None
                if ck.get("top_int"):
                    top = ck["top_int"][0]
                elif ck.get("top") is not None:
                    top = ck.get("top")
                if top is None:
                    return bounds
                bottom = ck.get("bottom")
                pn = int(pn)
                top_val = float(top)
                bottom_val = float(bottom) if bottom is not None else top_val
                if bottom_val < top_val:
                    top_val, bottom_val = bottom_val, top_val
                bounds[pn] = (top_val, bottom_val)
        except Exception:
            return {}
        return bounds