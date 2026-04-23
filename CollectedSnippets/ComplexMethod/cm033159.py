def getYMD(b):
    y, m, d = "", "", "01"
    if not b:
        return y, m, d
    b = turnTm2Dt(b)
    if re.match(r"[0-9]{4}", b):
        y = int(b[:4])
    r = re.search(r"[0-9]{4}.?([0-9]{1,2})", b)
    if r:
        m = r.group(1)
    r = re.search(r"[0-9]{4}.?[0-9]{,2}.?([0-9]{1,2})", b)
    if r:
        d = r.group(1)
    if not d or int(d) == 0 or int(d) > 31:
        d = "1"
    if not m or int(m) > 12 or int(m) < 1:
        m = "1"
    return y, m, d