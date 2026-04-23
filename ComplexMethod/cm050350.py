def _is_studio_custom(path):
    """
    Checks the to-be-imported records to see if there are any references to
    studio, which would mean that the module was created using studio

    Returns True if any of the records contains a context with the key
    studio in it, False if none of the records do
    """
    filepaths = []
    for level in os.walk(path):
        filepaths += [os.path.join(level[0], fn) for fn in level[2]]
    filepaths = [fp for fp in filepaths if fp.lower().endswith('.xml')]

    for fp in filepaths:
        root = lxml.etree.parse(fp).getroot()

        for record in root:
            # there might not be a context if it's a non-studio module
            try:
                # ast.literal_eval is like eval(), but safer
                # context is a string representing a python dict
                ctx = ast.literal_eval(record.get('context'))
                # there are no cases in which studio is false
                # so just checking for its existence is enough
                if ctx and ctx.get('studio'):
                    return True
            except Exception:
                continue
    return False