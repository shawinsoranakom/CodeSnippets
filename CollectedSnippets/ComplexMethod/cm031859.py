def makeunicodetype(unicode, trace):

    FILE = "Objects/unicodetype_db.h"

    print("--- Preparing", FILE, "...")

    # extract unicode types
    dummy = (0, 0, 0, 0, 0, 0)
    table = [dummy]
    cache = {dummy: 0}
    index = [0] * len(unicode.chars)
    numeric = {}
    spaces = []
    linebreaks = []
    extra_casing = []

    for char in unicode.chars:
        record = unicode.table[char]
        if record:
            # extract database properties
            category = record.general_category
            bidirectional = unicode.bidi_classes[char]
            properties = record.binary_properties
            flags = 0
            if category in ["Lm", "Lt", "Lu", "Ll", "Lo"]:
                flags |= ALPHA_MASK
            if "Lowercase" in properties:
                flags |= LOWER_MASK
            if 'Line_Break' in properties or bidirectional == "B":
                flags |= LINEBREAK_MASK
                linebreaks.append(char)
            if category == "Zs" or bidirectional in ("WS", "B", "S"):
                flags |= SPACE_MASK
                spaces.append(char)
            if category == "Lt":
                flags |= TITLE_MASK
            if "Uppercase" in properties:
                flags |= UPPER_MASK
            if char == ord(" ") or category[0] not in ("C", "Z"):
                flags |= PRINTABLE_MASK
            if "XID_Start" in properties:
                flags |= XID_START_MASK
            if "XID_Continue" in properties:
                flags |= XID_CONTINUE_MASK
            if "Cased" in properties:
                flags |= CASED_MASK
            if "Case_Ignorable" in properties:
                flags |= CASE_IGNORABLE_MASK
            sc = unicode.special_casing.get(char)
            cf = unicode.case_folding.get(char, [char])
            if record.simple_uppercase_mapping:
                upper = int(record.simple_uppercase_mapping, 16)
            else:
                upper = char
            if record.simple_lowercase_mapping:
                lower = int(record.simple_lowercase_mapping, 16)
            else:
                lower = char
            if record.simple_titlecase_mapping:
                title = int(record.simple_titlecase_mapping, 16)
            else:
                title = upper
            if sc is None and cf != [lower]:
                sc = ([lower], [title], [upper])
            if sc is None:
                if upper == lower == title:
                    upper = lower = title = 0
                else:
                    upper = upper - char
                    lower = lower - char
                    title = title - char
                    assert (abs(upper) <= 2147483647 and
                            abs(lower) <= 2147483647 and
                            abs(title) <= 2147483647)
            else:
                # This happens either when some character maps to more than one
                # character in uppercase, lowercase, or titlecase or the
                # casefolded version of the character is different from the
                # lowercase. The extra characters are stored in a different
                # array.
                flags |= EXTENDED_CASE_MASK
                lower = len(extra_casing) | (len(sc[0]) << 24)
                extra_casing.extend(sc[0])
                if cf != sc[0]:
                    lower |= len(cf) << 20
                    extra_casing.extend(cf)
                upper = len(extra_casing) | (len(sc[2]) << 24)
                extra_casing.extend(sc[2])
                # Title is probably equal to upper.
                if sc[1] == sc[2]:
                    title = upper
                else:
                    title = len(extra_casing) | (len(sc[1]) << 24)
                    extra_casing.extend(sc[1])
            # decimal digit, integer digit
            decimal = 0
            if record.decomposition_mapping:
                flags |= DECIMAL_MASK
                decimal = int(record.decomposition_mapping)
            digit = 0
            if record.numeric_type:
                flags |= DIGIT_MASK
                digit = int(record.numeric_type)
            if record.numeric_value:
                flags |= NUMERIC_MASK
                numeric.setdefault(record.numeric_value, []).append(char)
            item = (
                upper, lower, title, decimal, digit, flags
                )
            # add entry to index and item tables
            i = cache.get(item)
            if i is None:
                cache[item] = i = len(table)
                table.append(item)
            index[char] = i

    print(len(table), "unique character type entries")
    print(sum(map(len, numeric.values())), "numeric code points")
    print(len(spaces), "whitespace code points")
    print(len(linebreaks), "linebreak code points")
    print(len(extra_casing), "extended case array")

    print("--- Writing", FILE, "...")

    with open(FILE, "w") as fp:
        fprint = partial(print, file=fp)

        fprint("/* this file was generated by %s %s */" % (SCRIPT, VERSION))
        fprint()
        fprint("/* a list of unique character type descriptors */")
        fprint("const _PyUnicode_TypeRecord _PyUnicode_TypeRecords[] = {")
        for item in table:
            fprint("    {%d, %d, %d, %d, %d, %d}," % item)
        fprint("};")
        fprint()

        fprint("/* extended case mappings */")
        fprint()
        fprint("const Py_UCS4 _PyUnicode_ExtendedCase[] = {")
        for c in extra_casing:
            fprint("    %d," % c)
        fprint("};")
        fprint()

        # split decomposition index table
        index1, index2, shift = splitbins(index, trace)

        fprint("/* type indexes */")
        fprint("#define SHIFT", shift)
        Array("index1", index1).dump(fp, trace)
        Array("index2", index2).dump(fp, trace)

        # Generate code for _PyUnicode_ToNumeric()
        numeric_items = sorted(numeric.items())
        fprint('/* Returns the numeric value as double for Unicode characters')
        fprint(' * having this property, -1.0 otherwise.')
        fprint(' */')
        fprint('double _PyUnicode_ToNumeric(Py_UCS4 ch)')
        fprint('{')
        fprint('    switch (ch) {')
        for value, codepoints in numeric_items:
            # Turn text into float literals
            parts = value.split('/')
            parts = [repr(float(part)) for part in parts]
            value = '/'.join(parts)

            codepoints.sort()
            for codepoint in codepoints:
                fprint('    case 0x%04X:' % (codepoint,))
            fprint('        return (double) %s;' % (value,))
        fprint('    }')
        fprint('    return -1.0;')
        fprint('}')
        fprint()

        # Generate code for _PyUnicode_IsWhitespace()
        fprint("/* Returns 1 for Unicode characters having the bidirectional")
        fprint(" * type 'WS', 'B' or 'S' or the category 'Zs', 0 otherwise.")
        fprint(" */")
        fprint('int _PyUnicode_IsWhitespace(const Py_UCS4 ch)')
        fprint('{')
        fprint('    switch (ch) {')

        for codepoint in sorted(spaces):
            fprint('    case 0x%04X:' % (codepoint,))
        fprint('        return 1;')

        fprint('    }')
        fprint('    return 0;')
        fprint('}')
        fprint()

        # Generate code for _PyUnicode_IsLinebreak()
        fprint("/* Returns 1 for Unicode characters having the line break")
        fprint(" * property 'BK', 'CR', 'LF' or 'NL' or having bidirectional")
        fprint(" * type 'B', 0 otherwise.")
        fprint(" */")
        fprint('int _PyUnicode_IsLinebreak(const Py_UCS4 ch)')
        fprint('{')
        fprint('    switch (ch) {')
        for codepoint in sorted(linebreaks):
            fprint('    case 0x%04X:' % (codepoint,))
        fprint('        return 1;')

        fprint('    }')
        fprint('    return 0;')
        fprint('}')
        fprint()