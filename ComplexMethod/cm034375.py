def compute_diff(path, found_line, replace_or_add, state, key):
    diff = {
        'before_header': path,
        'after_header': path,
        'before': '',
        'after': '',
    }
    try:
        inf = open(path, "r")
    except FileNotFoundError:
        diff['before_header'] = '/dev/null'
    except OSError:
        pass
    else:
        diff['before'] = inf.read()
        inf.close()
    lines = diff['before'].splitlines(1)
    if (replace_or_add or state == 'absent') and found_line is not None and 1 <= found_line <= len(lines):
        del lines[found_line - 1]
    if state == 'present' and (replace_or_add or found_line is None):
        lines.append(key)
    diff['after'] = ''.join(lines)
    return diff