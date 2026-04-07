def fix_os_paths(x):
    if isinstance(x, str):
        return x.removeprefix(PATH).replace("\\", "/")
    elif isinstance(x, tuple):
        return tuple(fix_os_paths(list(x)))
    elif isinstance(x, list):
        return [fix_os_paths(y) for y in x]
    else:
        return x