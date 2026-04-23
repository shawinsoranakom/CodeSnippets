def join(path, /, *paths):
    path = os.fspath(path)
    if isinstance(path, bytes):
        sep = b'\\'
        seps = b'\\/'
        colon_seps = b':\\/'
    else:
        sep = '\\'
        seps = '\\/'
        colon_seps = ':\\/'
    try:
        result_drive, result_root, result_path = splitroot(path)
        for p in paths:
            p_drive, p_root, p_path = splitroot(p)
            if p_root:
                # Second path is absolute
                if p_drive or not result_drive:
                    result_drive = p_drive
                result_root = p_root
                result_path = p_path
                continue
            elif p_drive and p_drive != result_drive:
                if p_drive.lower() != result_drive.lower():
                    # Different drives => ignore the first path entirely
                    result_drive = p_drive
                    result_root = p_root
                    result_path = p_path
                    continue
                # Same drive in different case
                result_drive = p_drive
            # Second path is relative to the first
            if result_path and result_path[-1] not in seps:
                result_path = result_path + sep
            result_path = result_path + p_path
        ## add separator between UNC and non-absolute path
        if (result_path and not result_root and
            result_drive and result_drive[-1] not in colon_seps):
            return result_drive + sep + result_path
        return result_drive + result_root + result_path
    except (TypeError, AttributeError, BytesWarning):
        genericpath._check_arg_types('join', path, *paths)
        raise