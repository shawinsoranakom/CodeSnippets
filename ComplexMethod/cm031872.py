def main():
    print("Loading Mapping File...")
    gb2312map = open_mapping_file('python-mappings/GB2312.TXT', MAPPINGS_GB2312)
    cp936map = open_mapping_file('python-mappings/CP936.TXT', MAPPINGS_CP936)
    gb18030map = open_mapping_file('python-mappings/gb-18030-2000.xml', MAPPINGS_GB18030)

    gb18030decmap, gb18030unilinear = parse_gb18030map(gb18030map)
    gbkdecmap = loadmap(cp936map)
    gb2312decmap = loadmap(gb2312map)
    difmap = {}
    for c1, m in gbkdecmap.items():
        for c2, code in m.items():
            del gb18030decmap[c1][c2]
            if not gb18030decmap[c1]:
                del gb18030decmap[c1]
    for c1, m in gb2312decmap.items():
        for c2, code in m.items():
            gbkc1, gbkc2 = c1 | 0x80, c2 | 0x80
            if gbkdecmap[gbkc1][gbkc2] == code:
                del gbkdecmap[gbkc1][gbkc2]
                if not gbkdecmap[gbkc1]:
                    del gbkdecmap[gbkc1]

    gb2312_gbkencmap, gb18030encmap = {}, {}
    for c1, m in gbkdecmap.items():
        for c2, code in m.items():
            gb2312_gbkencmap.setdefault(code >> 8, {})
            gb2312_gbkencmap[code >> 8][code & 0xff] = c1 << 8 | c2 # MSB set
    for c1, m in gb2312decmap.items():
        for c2, code in m.items():
            gb2312_gbkencmap.setdefault(code >> 8, {})
            gb2312_gbkencmap[code >> 8][code & 0xff] = c1 << 8 | c2 # MSB unset
    for c1, m in gb18030decmap.items():
        for c2, code in m.items():
            gb18030encmap.setdefault(code >> 8, {})
            gb18030encmap[code >> 8][code & 0xff] = c1 << 8 | c2

    with open('mappings_cn.h', 'w') as fp:
        print_autogen(fp, os.path.basename(__file__))

        print("Generating GB2312 decode map...")
        writer = DecodeMapWriter(fp, "gb2312", gb2312decmap)
        writer.update_decode_map(GB2312_C1, GB2312_C2)
        writer.generate()

        print("Generating GBK decode map...")
        writer = DecodeMapWriter(fp, "gbkext", gbkdecmap)
        writer.update_decode_map(GBKL1_C1, GBKL1_C2)
        writer.update_decode_map(GBKL2_C1, GBKL2_C2)
        writer.generate()

        print("Generating GB2312 && GBK encode map...")
        writer = EncodeMapWriter(fp, "gbcommon", gb2312_gbkencmap)
        writer.generate()

        print("Generating GB18030 extension decode map...")
        writer = DecodeMapWriter(fp, "gb18030ext", gb18030decmap)
        for i in range(1, 6):
            writer.update_decode_map(eval("GB18030EXTP%d_C1" % i), eval("GB18030EXTP%d_C2" % i))

        writer.generate()

        print("Generating GB18030 extension encode map...")
        writer = EncodeMapWriter(fp, "gb18030ext", gb18030encmap)
        writer.generate()

        print("Generating GB18030 Unicode BMP Mapping Ranges...")
        ranges = [[-1, -1, -1]]
        gblinnum = 0
        fp.write("""
static const struct _gb18030_to_unibmp_ranges {
    Py_UCS4   first, last;
    DBCHAR       base;
} gb18030_to_unibmp_ranges[] = {
""")

        for uni in gb18030unilinear:
            if uni == ranges[-1][1] + 1:
                ranges[-1][1] = uni
            else:
                ranges.append([uni, uni, gblinnum])
            gblinnum += 1

        filler = BufferedFiller()
        for first, last, base in ranges[1:]:
            filler.write('{', str(first), ',', str(last), ',', str(base), '},')

        filler.write('{', '0,', '0,', str(
            ranges[-1][2] + ranges[-1][1] - ranges[-1][0] + 1), '}', '};')
        filler.printout(fp)

    print("Done!")