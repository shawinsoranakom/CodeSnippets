def parse_struct_body(source, anon_name, parent):
    done = False
    while not done:
        done = True
        for srcinfo in source:
            m = STRUCT_MEMBER_RE.match(srcinfo.text)
            if m:
                break
        else:
            # We ran out of lines.
            if srcinfo is not None:
                srcinfo.done()
            return
        for item in _parse_struct_next(m, srcinfo, anon_name, parent):
            if callable(item):
                parse_body = item
                yield from parse_body(source)
            else:
                yield item
            done = False