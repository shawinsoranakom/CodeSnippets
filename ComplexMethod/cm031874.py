def main_tw():
    big5decmap, big5encmap = load_big5_map()
    cp950decmap, cp950encmap = load_cp950_map()

    # CP950 extends Big5, and the codec can use the Big5 lookup tables
    # for most entries. So the CP950 tables should only include entries
    # that are not in Big5:
    for c1, m in list(cp950encmap.items()):
        for c2, code in list(m.items()):
            if (c1 in big5encmap and c2 in big5encmap[c1]
                    and big5encmap[c1][c2] == code):
                del cp950encmap[c1][c2]
    for c1, m in list(cp950decmap.items()):
        for c2, code in list(m.items()):
            if (c1 in big5decmap and c2 in big5decmap[c1]
                    and big5decmap[c1][c2] == code):
                del cp950decmap[c1][c2]

    with open('mappings_tw.h', 'w') as fp:
        print_autogen(fp, os.path.basename(__file__))
        write_big5_maps(fp, 'BIG5', 'big5', big5decmap, big5encmap)
        write_big5_maps(fp, 'CP950', 'cp950ext', cp950decmap, cp950encmap)