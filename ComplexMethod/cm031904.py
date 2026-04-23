def parse_function_statics(source, func, anon_name):
    # For now we do not worry about locals declared in for loop "headers".
    depth = 1;
    while depth > 0:
        for srcinfo in source:
            m = LOCAL_STATICS_RE.match(srcinfo.text)
            if m:
                break
        else:
            # We ran out of lines.
            if srcinfo is not None:
                srcinfo.done()
            return
        for item, depth in _parse_next_local_static(m, srcinfo,
                                                    anon_name, func, depth):
            if callable(item):
                parse_body = item
                yield from parse_body(source)
            elif item is not None:
                yield item