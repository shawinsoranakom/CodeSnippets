def loadmap_jisx0213(fo):
    decmap3, decmap4 = {}, {} # maps to BMP for level 3 and 4
    decmap3_2, decmap4_2 = {}, {} # maps to U+2xxxx for level 3 and 4
    decmap3_pair = {} # maps to BMP-pair for level 3
    for line in fo:
        line = line.split('#', 1)[0].strip()
        if not line or len(line.split()) < 2:
            continue

        row = line.split()
        loc = eval('0x' + row[0][2:])
        level = eval(row[0][0])
        m = None
        if len(row[1].split('+')) == 2: # single unicode
            uni = eval('0x' + row[1][2:])
            if level == 3:
                if uni < 0x10000:
                    m = decmap3
                elif 0x20000 <= uni < 0x30000:
                    uni -= 0x20000
                    m = decmap3_2
            elif level == 4:
                if uni < 0x10000:
                    m = decmap4
                elif 0x20000 <= uni < 0x30000:
                    uni -= 0x20000
                    m = decmap4_2
            m.setdefault((loc >> 8), {})
            m[(loc >> 8)][(loc & 0xff)] = uni
        else: # pair
            uniprefix = eval('0x' + row[1][2:6]) # body
            uni = eval('0x' + row[1][7:11]) # modifier
            if level != 3:
                raise ValueError("invalid map")
            decmap3_pair.setdefault(uniprefix, {})
            m = decmap3_pair[uniprefix]

        if m is None:
            raise ValueError("invalid map")
        m.setdefault((loc >> 8), {})
        m[(loc >> 8)][(loc & 0xff)] = uni

    return decmap3, decmap4, decmap3_2, decmap4_2, decmap3_pair