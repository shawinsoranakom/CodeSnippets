def parse_resolution(s, *, lenient=False):
    if s is None:
        return {}

    if lenient:
        mobj = re.search(r'(?P<w>\d+)\s*[xX×,]\s*(?P<h>\d+)', s)
    else:
        mobj = re.search(r'(?<![a-zA-Z0-9])(?P<w>\d+)\s*[xX×,]\s*(?P<h>\d+)(?![a-zA-Z0-9])', s)
    if mobj:
        return {
            'width': int(mobj.group('w')),
            'height': int(mobj.group('h')),
        }

    mobj = re.search(r'(?<![a-zA-Z0-9])(\d+)[pPiI](?![a-zA-Z0-9])', s)
    if mobj:
        return {'height': int(mobj.group(1))}

    mobj = re.search(r'\b([48])[kK]\b', s)
    if mobj:
        return {'height': int(mobj.group(1)) * 540}

    if lenient:
        mobj = re.search(r'(?<!\d)(\d{2,5})w(?![a-zA-Z0-9])', s)
        if mobj:
            return {'width': int(mobj.group(1))}

    return {}