def parse_docstring(docstring):
    """
    Parse out the parts of a docstring. Return (title, body, metadata).
    """
    if not docstring:
        return "", "", {}
    docstring = cleandoc(docstring)
    parts = re.split(r"\n{2,}", docstring)
    title = parts[0]
    if len(parts) == 1:
        body = ""
        metadata = {}
    else:
        parser = HeaderParser()
        try:
            metadata = parser.parsestr(parts[-1])
        except HeaderParseError:
            metadata = {}
            body = "\n\n".join(parts[1:])
        else:
            metadata = dict(metadata.items())
            if metadata:
                body = "\n\n".join(parts[1:-1])
            else:
                body = "\n\n".join(parts[1:])
    return title, body, metadata