def get_prog(spec=None, *, absolute=False, allowsuffix=True):
    if spec is None:
        _, spec = _find_script()
        # This is more natural for prog than __file__ would be.
        filename = sys.argv[0]
    elif isinstance(spec, str):
        filename = os.path.normpath(spec)
        spec = None
    else:
        filename = spec.origin
    if _is_standalone(filename):
        # Check if "installed".
        if allowsuffix or not filename.endswith('.py'):
            basename = os.path.basename(filename)
            found = shutil.which(basename)
            if found:
                script = os.path.abspath(filename)
                found = os.path.abspath(found)
                if os.path.normcase(script) == os.path.normcase(found):
                    return basename
        # It is only "standalone".
        if absolute:
            filename = os.path.abspath(filename)
        return filename
    elif spec is not None:
        module = spec.name
        if module.endswith('.__main__'):
            module = module[:-9]
        return f'{sys.executable} -m {module}'
    else:
        if absolute:
            filename = os.path.abspath(filename)
        return f'{sys.executable} {filename}'