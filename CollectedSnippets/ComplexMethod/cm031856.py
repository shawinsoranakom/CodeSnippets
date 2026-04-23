def python_tabledef_code(varname, map, comments=1, key_precision=2):

    l = []
    append = l.append
    append('%s = (' % varname)

    # Analyze map and create table dict
    mappings = sorted(map.items())
    table = {}
    maxkey = 255
    if 'IDENTITY' in map:
        for key in range(256):
            table[key] = (key, '')
        del map['IDENTITY']
    for mapkey, mapvalue in mappings:
        mapcomment = ''
        if isinstance(mapkey, tuple):
            (mapkey, mapcomment) = mapkey
        if isinstance(mapvalue, tuple):
            (mapvalue, mapcomment) = mapvalue
        if mapkey == MISSING_CODE:
            continue
        table[mapkey] = (mapvalue, mapcomment)
        if mapkey > maxkey:
            maxkey = mapkey
    if maxkey > MAX_TABLE_SIZE:
        # Table too large
        return None

    # Create table code
    maxchar = 0
    for key in range(maxkey + 1):
        if key not in table:
            mapvalue = MISSING_CODE
            mapcomment = 'UNDEFINED'
        else:
            mapvalue, mapcomment = table[key]
        if mapvalue == MISSING_CODE:
            mapchar = UNI_UNDEFINED
        else:
            if isinstance(mapvalue, tuple):
                # 1-n mappings not supported
                return None
            else:
                mapchar = chr(mapvalue)
        maxchar = max(maxchar, ord(mapchar))
        if mapcomment and comments:
            append('    %a \t#  %s -> %s' % (mapchar,
                                            hexrepr(key, key_precision),
                                            mapcomment))
        else:
            append('    %a' % mapchar)

    if maxchar < 256:
        append('    %a \t## Widen to UCS2 for optimization' % UNI_UNDEFINED)
    append(')')
    return l