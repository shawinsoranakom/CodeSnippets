def make_hkscs_map(table):
    decode_map = {}
    encode_map_bmp, encode_map_notbmp = {}, {}
    is_bmp_map = {}
    sequences = []
    beginnings = {}
    single_cp_table = []
    # Determine multi-codepoint sequences, and sequence beginnings that encode
    # multiple multibyte (i.e. Big-5) codes.
    for mbcode, cp_seq in table:
        cp, *_ = cp_seq
        if len(cp_seq) == 1:
            single_cp_table.append((mbcode, cp))
        else:
            sequences.append((mbcode, cp_seq))
        beginnings.setdefault(cp, []).append(mbcode)
    # Decode table only cares about single code points (no sequences) currently
    for mbcode, cp in single_cp_table:
        b1, b2 = split_bytes(mbcode)
        decode_map.setdefault(b1, {})
        decode_map[b1][b2] = cp & 0xffff
    # Encode table needs to mark code points beginning a sequence as tuples.
    for cp, mbcodes in beginnings.items():
        plane = cp >> 16
        if plane == 0:
            encode_map = encode_map_bmp
        elif plane == 2:
            encode_map = encode_map_notbmp
            is_bmp_map[bh2s(mbcodes[0])] = 1
        else:
            assert False, 'only plane 0 (BMP) and plane 2 (SIP) allowed'
        if len(mbcodes) == 1:
            encode_value = mbcodes[0]
        else:
            encode_value = tuple(mbcodes)
        uni_b1, uni_b2 = split_bytes(cp & 0xffff)
        encode_map.setdefault(uni_b1, {})
        encode_map[uni_b1][uni_b2] = encode_value

    return decode_map, encode_map_bmp, encode_map_notbmp, is_bmp_map