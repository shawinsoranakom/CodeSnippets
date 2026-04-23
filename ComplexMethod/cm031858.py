def makeunicodedata(unicode, trace):

    # the default value of east_asian_width is "N", for unassigned code points
    # not mentioned in EastAsianWidth.txt
    # in addition there are some reserved but unassigned code points in CJK
    # ranges that are classified as "W". code points in private use areas
    # have a width of "A". both of these have entries in
    # EastAsianWidth.txt
    # see https://unicode.org/reports/tr11/#Unassigned
    assert EASTASIANWIDTH_NAMES[0] == "N"
    assert GRAPHEME_CLUSTER_NAMES[0] == "Other"
    assert INDIC_CONJUNCT_BREAK_NAMES[0] == "None"
    dummy = (0, 0, 0, 0, 0, 0, 0, 0, 0)
    table = [dummy]
    cache = {0: dummy}
    index = [0] * len(unicode.chars)

    FILE = "Modules/unicodedata_db.h"

    print("--- Preparing", FILE, "...")

    # 1) database properties

    for char in unicode.chars:
        record = unicode.table[char]
        eastasianwidth = EASTASIANWIDTH_NAMES.index(unicode.widths[char] or 'N')
        graphemebreak = GRAPHEME_CLUSTER_NAMES.index(unicode.grapheme_breaks[char] or 'Other')
        extpict = unicode.ext_picts[char]
        bidirectional = BIDIRECTIONAL_NAMES.index(unicode.bidi_classes[char])
        if record:
            # extract database properties
            category = CATEGORY_NAMES.index(record.general_category)
            combining = int(record.canonical_combining_class)
            mirrored = record.bidi_mirrored == "Y"
            normalizationquickcheck = record.quick_check
            incb = INDIC_CONJUNCT_BREAK_NAMES.index(record.incb)
            item = (
                category, combining, bidirectional, mirrored, eastasianwidth,
                normalizationquickcheck, graphemebreak, incb, extpict,
                )
        else:
            if eastasianwidth or graphemebreak or extpict or bidirectional:
                item = (0, 0, bidirectional, 0, eastasianwidth,
                        0, graphemebreak, 0, extpict)
            else:
                continue

        # add entry to index and item tables
        i = cache.get(item)
        if i is None:
            cache[item] = i = len(table)
            table.append(item)
        index[char] = i

    # 2) decomposition data

    decomp_data_cache = {}
    decomp_data = [0]
    decomp_prefix = [""]
    decomp_index = [0] * len(unicode.chars)
    decomp_size = 0

    comp_pairs = []
    comp_first = [None] * len(unicode.chars)
    comp_last = [None] * len(unicode.chars)

    for char in unicode.chars:
        record = unicode.table[char]
        if record:
            if record.decomposition_type:
                decomp = record.decomposition_type.split()
                if len(decomp) > 19:
                    raise Exception("character %x has a decomposition too large for nfd_nfkd" % char)
                # prefix
                if decomp[0][0] == "<":
                    prefix = decomp.pop(0)
                else:
                    prefix = ""
                try:
                    i = decomp_prefix.index(prefix)
                except ValueError:
                    i = len(decomp_prefix)
                    decomp_prefix.append(prefix)
                prefix = i
                assert prefix < 256
                # content
                decomp = [prefix + (len(decomp)<<8)] + [int(s, 16) for s in decomp]
                # Collect NFC pairs
                if not prefix and len(decomp) == 3 and \
                   char not in unicode.exclusions and \
                   unicode.table[decomp[1]].canonical_combining_class == "0":
                    p, l, r = decomp
                    comp_first[l] = 1
                    comp_last[r] = 1
                    comp_pairs.append((l,r,char))
                key = tuple(decomp)
                i = decomp_data_cache.get(key, -1)
                if i == -1:
                    i = len(decomp_data)
                    decomp_data.extend(decomp)
                    decomp_size = decomp_size + len(decomp) * 2
                    decomp_data_cache[key] = i
                else:
                    assert decomp_data[i:i+len(decomp)] == decomp
            else:
                i = 0
            decomp_index[char] = i

    f = l = 0
    comp_first_ranges = []
    comp_last_ranges = []
    prev_f = prev_l = None
    for i in unicode.chars:
        if comp_first[i] is not None:
            comp_first[i] = f
            f += 1
            if prev_f is None:
                prev_f = (i,i)
            elif prev_f[1]+1 == i:
                prev_f = prev_f[0],i
            else:
                comp_first_ranges.append(prev_f)
                prev_f = (i,i)
        if comp_last[i] is not None:
            comp_last[i] = l
            l += 1
            if prev_l is None:
                prev_l = (i,i)
            elif prev_l[1]+1 == i:
                prev_l = prev_l[0],i
            else:
                comp_last_ranges.append(prev_l)
                prev_l = (i,i)
    comp_first_ranges.append(prev_f)
    comp_last_ranges.append(prev_l)
    total_first = f
    total_last = l

    comp_data = [0]*(total_first*total_last)
    for f,l,char in comp_pairs:
        f = comp_first[f]
        l = comp_last[l]
        comp_data[f*total_last+l] = char

    print(len(table), "unique properties")
    print(len(decomp_prefix), "unique decomposition prefixes")
    print(len(decomp_data), "unique decomposition entries:", end=' ')
    print(decomp_size, "bytes")
    print(total_first, "first characters in NFC")
    print(total_last, "last characters in NFC")
    print(len(comp_pairs), "NFC pairs")

    print("--- Writing", FILE, "...")

    with open(FILE, "w") as fp:
        fprint = partial(print, file=fp)

        fprint("/* this file was generated by %s %s */" % (SCRIPT, VERSION))
        fprint()
        fprint('#define UNIDATA_VERSION "%s"' % UNIDATA_VERSION)
        fprint("/* a list of unique database records */")
        fprint("const _PyUnicode_DatabaseRecord _PyUnicode_Database_Records[] = {")
        for item in table:
            fprint("    {%d, %d, %d, %d, %d, %d, %d, %d, %d}," % item)
        fprint("};")
        fprint()

        fprint("/* Reindexing of NFC first characters. */")
        fprint("#define TOTAL_FIRST",total_first)
        fprint("#define TOTAL_LAST",total_last)
        fprint("struct reindex{int start;short count,index;};")
        fprint("static struct reindex nfc_first[] = {")
        for start,end in comp_first_ranges:
            fprint("    { %d, %d, %d}," % (start,end-start,comp_first[start]))
        fprint("    {0,0,0}")
        fprint("};\n")
        fprint("static struct reindex nfc_last[] = {")
        for start,end in comp_last_ranges:
            fprint("  { %d, %d, %d}," % (start,end-start,comp_last[start]))
        fprint("  {0,0,0}")
        fprint("};\n")

        # FIXME: <fl> the following tables could be made static, and
        # the support code moved into unicodedatabase.c

        fprint("/* string literals */")
        fprint("const char *_PyUnicode_CategoryNames[] = {")
        for name in CATEGORY_NAMES:
            fprint("    \"%s\"," % name)
        fprint("    NULL")
        fprint("};")

        fprint("const char *_PyUnicode_BidirectionalNames[] = {")
        for name in BIDIRECTIONAL_NAMES:
            fprint("    \"%s\"," % name)
        fprint("    NULL")
        fprint("};")

        fprint("const char *_PyUnicode_EastAsianWidthNames[] = {")
        for name in EASTASIANWIDTH_NAMES:
            fprint("    \"%s\"," % name)
        fprint("    NULL")
        fprint("};")

        for i, name in enumerate(GRAPHEME_CLUSTER_NAMES):
            fprint("#define GCB_%s %d" % (name, i))

        fprint("const char * const _PyUnicode_GraphemeBreakNames[] = {")
        for name in GRAPHEME_CLUSTER_NAMES:
            fprint('    "%s",' % name)
        fprint("    NULL")
        fprint("};")

        for i, name in enumerate(INDIC_CONJUNCT_BREAK_NAMES):
            fprint("#define InCB_%s %d" % (name, i))

        fprint("const char * const _PyUnicode_IndicConjunctBreakNames[] = {")
        for name in INDIC_CONJUNCT_BREAK_NAMES:
            fprint('    "%s",' % name)
        fprint("    NULL")
        fprint("};")

        # Generate block tables
        names = []
        name_to_index = {}
        blocks = []
        for start, end, name in unicode.blocks:
            if name not in name_to_index:
                name_to_index[name] = len(names)
                names.append(name)
            blocks.append((start, end, name_to_index[name]))

        fprint("static const char * const _PyUnicode_BlockNames[] = {")
        for name in names:
            fprint('    "%s",' % name)
        fprint("};")

        fprint("typedef struct {")
        fprint("    Py_UCS4 start;")
        fprint("    Py_UCS4 end;")
        fprint("    unsigned short name;")
        fprint("} _PyUnicode_Block;")

        fprint("static const _PyUnicode_Block _PyUnicode_Blocks[] = {")
        for start, end, name in blocks:
            fprint("    {0x%04X, 0x%04X, %d}," % (start, end, name))
        fprint("};")
        fprint(f"#define BLOCK_COUNT {len(blocks)}")
        fprint()

        fprint("static const char *decomp_prefix[] = {")
        for name in decomp_prefix:
            fprint("    \"%s\"," % name)
        fprint("    NULL")
        fprint("};")

        # split record index table
        index1, index2, shift = splitbins(index, trace)

        fprint("/* index tables for the database records */")
        fprint("#define SHIFT", shift)
        Array("index1", index1).dump(fp, trace)
        Array("index2", index2).dump(fp, trace)

        # split decomposition index table
        index1, index2, shift = splitbins(decomp_index, trace)

        fprint("/* decomposition data */")
        Array("decomp_data", decomp_data).dump(fp, trace)

        fprint("/* index tables for the decomposition data */")
        fprint("#define DECOMP_SHIFT", shift)
        Array("decomp_index1", index1).dump(fp, trace)
        Array("decomp_index2", index2).dump(fp, trace)

        index, index2, shift = splitbins(comp_data, trace)
        fprint("/* NFC pairs */")
        fprint("#define COMP_SHIFT", shift)
        Array("comp_index", index).dump(fp, trace)
        Array("comp_data", index2).dump(fp, trace)

        # Generate delta tables for old versions
        for version, table, normalization in unicode.changed:
            cversion = version.replace(".","_")
            records = [table[0]]
            cache = {table[0]:0}
            index = [0] * len(table)
            for i, record in enumerate(table):
                try:
                    index[i] = cache[record]
                except KeyError:
                    index[i] = cache[record] = len(records)
                    records.append(record)
            index1, index2, shift = splitbins(index, trace)
            fprint("static const change_record change_records_%s[] = {" % cversion)
            for record in records:
                fprint("    { %s }," % ", ".join(map(str,record)))
            fprint("};")
            Array("changes_%s_index" % cversion, index1).dump(fp, trace)
            Array("changes_%s_data" % cversion, index2).dump(fp, trace)
            fprint("static const change_record* get_change_%s(Py_UCS4 n)" % cversion)
            fprint("{")
            fprint("    int index;")
            fprint("    if (n >= 0x110000) index = 0;")
            fprint("    else {")
            fprint("        index = changes_%s_index[n>>%d];" % (cversion, shift))
            fprint("        index = changes_%s_data[(index<<%d)+(n & %d)];" % \
                   (cversion, shift, ((1<<shift)-1)))
            fprint("    }")
            fprint("    return change_records_%s+index;" % cversion)
            fprint("}\n")
            fprint("static Py_UCS4 normalization_%s(Py_UCS4 n)" % cversion)
            fprint("{")
            fprint("    switch(n) {")
            for k, v in normalization:
                fprint("    case %s: return 0x%s;" % (hex(k), v))
            fprint("    default: return 0;")
            fprint("    }\n}\n")