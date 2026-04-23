def sanitize_path(s, force=False):
    """Sanitizes and normalizes path on Windows"""
    if sys.platform != 'win32':
        if not force:
            return s
        root = '/' if s.startswith('/') else ''
        path = '/'.join(_sanitize_path_parts(s.split('/')))
        return root + path if root or path else '.'

    normed = s.replace('/', '\\')

    if normed.startswith('\\\\'):
        # UNC path (`\\SERVER\SHARE`) or device path (`\\.`, `\\?`)
        parts = normed.split('\\')
        root = '\\'.join(parts[:4]) + '\\'
        parts = parts[4:]
    elif normed[1:2] == ':':
        # absolute path or drive relative path
        offset = 3 if normed[2:3] == '\\' else 2
        root = normed[:offset]
        parts = normed[offset:].split('\\')
    else:
        # relative/drive root relative path
        root = '\\' if normed[:1] == '\\' else ''
        parts = normed.split('\\')

    path = '\\'.join(_sanitize_path_parts(parts))
    return root + path if root or path else '.'