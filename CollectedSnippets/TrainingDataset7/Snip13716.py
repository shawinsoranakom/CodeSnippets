def find_top_level(top_level):
    # Try to be a bit smarter than unittest about finding the default top-level
    # for a given directory path, to avoid breaking relative imports.
    # (Unittest's default is to set top-level equal to the path, which means
    # relative imports will result in "Attempted relative import in
    # non-package.").

    # We'd be happy to skip this and require dotted module paths (which don't
    # cause this problem) instead of file paths (which do), but in the case of
    # a directory in the cwd, which would be equally valid if considered as a
    # top-level module or as a directory path, unittest unfortunately prefers
    # the latter.
    while True:
        init_py = os.path.join(top_level, "__init__.py")
        if not os.path.exists(init_py):
            break
        try_next = os.path.dirname(top_level)
        if try_next == top_level:
            # __init__.py all the way down? give up.
            break
        top_level = try_next
    return top_level