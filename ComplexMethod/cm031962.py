def _normalize_table_file_props(header, sep):
    if not header:
        return None, sep

    if not isinstance(header, str):
        if not sep:
            raise NotImplementedError(header)
        header = sep.join(header)
    elif not sep:
        for sep in ('\t', ',', ' '):
            if sep in header:
                break
        else:
            sep = None
    return header, sep