def extract_position(ck):
        pn = None
        top = None
        left = None
        try:
            if ck.get("page_num_int"):
                pn = ck["page_num_int"][0]
            elif ck.get("page_number") is not None:
                pn = ck.get("page_number")

            if ck.get("top_int"):
                top = ck["top_int"][0]
            elif ck.get("top") is not None:
                top = ck.get("top")

            if ck.get("position_int"):
                left = ck["position_int"][0][1]
            elif ck.get("x0") is not None:
                left = ck.get("x0")
        except Exception:
            pn = top = left = None
        return pn, top, left