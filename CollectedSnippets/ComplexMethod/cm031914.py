def _resolve_samefile(filename, pattern, suffix):
    if pattern == filename:
        return None
    if pattern.endswith(os.path.sep):
        pattern += f'*{suffix}'
    assert os.path.normpath(pattern) == pattern, (pattern,)
    if '*' in os.path.dirname(pattern):
        raise NotImplementedError((filename, pattern))
    if '*' not in os.path.basename(pattern):
        return pattern

    common = os.path.commonpath([filename, pattern])
    relpattern = pattern[len(common) + len(os.path.sep):]
    relpatterndir = os.path.dirname(relpattern)
    relfile = filename[len(common) + len(os.path.sep):]
    if os.path.basename(pattern) == '*':
        return os.path.join(common, relpatterndir, relfile)
    elif os.path.basename(relpattern) == '*' + suffix:
        return os.path.join(common, relpatterndir, relfile)
    else:
        raise NotImplementedError((filename, pattern))