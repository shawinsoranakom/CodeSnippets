def python_mapdef_code(varname, map, comments=1, precisions=(2, 4)):

    l = []
    append = l.append
    if "IDENTITY" in map:
        append("%s = codecs.make_identity_dict(range(%d))" %
               (varname, map["IDENTITY"]))
        append("%s.update({" % varname)
        splits = 1
        del map["IDENTITY"]
        identity = 1
    else:
        append("%s = {" % varname)
        splits = 0
        identity = 0

    mappings = sorted(map.items())
    i = 0
    key_precision, value_precision = precisions
    for mapkey, mapvalue in mappings:
        mapcomment = ''
        if isinstance(mapkey, tuple):
            (mapkey, mapcomment) = mapkey
        if isinstance(mapvalue, tuple):
            (mapvalue, mapcomment) = mapvalue
        if mapkey is None:
            continue
        if (identity and
            mapkey == mapvalue and
            mapkey < 256):
            # No need to include identity mappings, since these
            # are already set for the first 256 code points.
            continue
        key = hexrepr(mapkey, key_precision)
        value = hexrepr(mapvalue, value_precision)
        if mapcomment and comments:
            append('    %s: %s,\t#  %s' % (key, value, mapcomment))
        else:
            append('    %s: %s,' % (key, value))
        i += 1
        if i == 4096:
            # Split the definition into parts to that the Python
            # parser doesn't dump core
            if splits == 0:
                append('}')
            else:
                append('})')
            append('%s.update({' % varname)
            i = 0
            splits = splits + 1
    if splits == 0:
        append('}')
    else:
        append('})')

    return l