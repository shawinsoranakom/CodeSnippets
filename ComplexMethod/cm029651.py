def _match_filename(pattern, filename, *, MS_WINDOWS=(sys.platform == 'win32')):
    if not filename:
        return pattern.match('<unknown>') is not None
    if filename[0] == '<' and filename[-1] == '>':
        return pattern.match(filename) is not None

    is_py = (filename[-3:].lower() == '.py'
             if MS_WINDOWS else
             filename.endswith('.py'))
    if is_py:
        filename = filename[:-3]
    if pattern.match(filename):  # for backward compatibility
        return True
    if MS_WINDOWS:
        if not is_py and filename[-4:].lower() == '.pyw':
            filename = filename[:-4]
            is_py = True
        if is_py and filename[-9:].lower() in (r'\__init__', '/__init__'):
            filename = filename[:-9]
        filename = filename.replace('\\', '/')
    else:
        if is_py and filename.endswith('/__init__'):
            filename = filename[:-9]
    filename = filename.replace('/', '.')
    i = 0
    while True:
        if pattern.match(filename, i):
            return True
        i = filename.find('.', i) + 1
        if not i:
            return False