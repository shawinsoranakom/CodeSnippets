def nameprep(label):  # type: (str) -> str
    # Map
    newlabel = []
    for c in label:
        if stringprep.in_table_b1(c):
            # Map to nothing
            continue
        newlabel.append(stringprep.map_table_b2(c))
    label = "".join(newlabel)

    # Normalize
    label = unicodedata.normalize("NFKC", label)

    # Prohibit
    for i, c in enumerate(label):
        if stringprep.in_table_c12(c) or \
           stringprep.in_table_c22(c) or \
           stringprep.in_table_c3(c) or \
           stringprep.in_table_c4(c) or \
           stringprep.in_table_c5(c) or \
           stringprep.in_table_c6(c) or \
           stringprep.in_table_c7(c) or \
           stringprep.in_table_c8(c) or \
           stringprep.in_table_c9(c):
            raise UnicodeEncodeError("idna", label, i, i+1, f"Invalid character {c!r}")

    # Check bidi
    RandAL = [stringprep.in_table_d1(x) for x in label]
    if any(RandAL):
        # There is a RandAL char in the string. Must perform further
        # tests:
        # 1) The characters in section 5.8 MUST be prohibited.
        # This is table C.8, which was already checked
        # 2) If a string contains any RandALCat character, the string
        # MUST NOT contain any LCat character.
        for i, x in enumerate(label):
            if stringprep.in_table_d2(x):
                raise UnicodeEncodeError("idna", label, i, i+1,
                                         "Violation of BIDI requirement 2")
        # 3) If a string contains any RandALCat character, a
        # RandALCat character MUST be the first character of the
        # string, and a RandALCat character MUST be the last
        # character of the string.
        if not RandAL[0]:
            raise UnicodeEncodeError("idna", label, 0, 1,
                                     "Violation of BIDI requirement 3")
        if not RandAL[-1]:
            raise UnicodeEncodeError("idna", label, len(label)-1, len(label),
                                     "Violation of BIDI requirement 3")

    return label