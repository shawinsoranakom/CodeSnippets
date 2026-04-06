def output(is_bsd):
    if is_bsd:
        return "touch: /a/b/c: No such file or directory"
    return "touch: cannot touch '/a/b/c': No such file or directory"