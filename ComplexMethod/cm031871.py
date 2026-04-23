def parse_gb18030map(fo):
    m, gbuni = {}, {}
    for i in range(65536):
        if i < 0xd800 or i > 0xdfff: # exclude unicode surrogate area
            gbuni[i] = None
    for uni, native in re_gb18030ass.findall(fo.read()):
        uni = eval('0x'+uni)
        native = [eval('0x'+u) for u in native.split()]
        if len(native) <= 2:
            del gbuni[uni]
        if len(native) == 2: # we can decode algorithmically for 1 or 4 bytes
            m.setdefault(native[0], {})
            m[native[0]][native[1]] = uni
    gbuni = [k for k in gbuni.keys()]
    gbuni.sort()
    return m, gbuni