def _parse_line(line, prev=None):
    last = line
    if prev:
        if not prev.endswith(os.linesep):
            prev += os.linesep
        line = prev + line
    m = CAPI_RE.match(line)
    if not m:
        if not prev and line.startswith('static inline '):
            return line  # the new "prev"
        #if 'PyAPI_' in line or '#define ' in line or ' define ' in line:
        #    print(line)
        return None
    results = zip(KINDS, m.groups())
    for kind, name in results:
        if name:
            clean = last.split('//')[0].rstrip()
            if clean.endswith('*/'):
                clean = clean.split('/*')[0].rstrip()

            if kind == 'macro' or kind == 'constant':
                if not clean.endswith('\\'):
                    return name, kind
            elif kind == 'inline':
                if clean.endswith('}'):
                    if not prev or clean == '}':
                        return name, kind
            elif kind == 'func' or kind == 'data':
                if clean.endswith(';'):
                    return name, kind
            else:
                # This should not be reached.
                raise NotImplementedError
            return line  # the new "prev"
    # It was a plain #define.
    return None