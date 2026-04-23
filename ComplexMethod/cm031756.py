def getFilesForName(name):
    """Get a list of module files for a filename, a module or package name,
    or a directory.
    """
    if not os.path.exists(name):
        # check for glob chars
        if containsAny(name, "*?[]"):
            files = glob.glob(name)
            list = []
            for file in files:
                list.extend(getFilesForName(file))
            return list

        # try to find module or package
        try:
            spec = importlib.util.find_spec(name)
            name = spec.origin
        except ImportError:
            name = None
        if not name:
            return []

    if os.path.isdir(name):
        # find all python files in directory
        list = []
        # get extension for python source files
        _py_ext = importlib.machinery.SOURCE_SUFFIXES[0]
        for root, dirs, files in os.walk(name):
            # don't recurse into CVS directories
            if 'CVS' in dirs:
                dirs.remove('CVS')
            # add all *.py files to list
            list.extend(
                [os.path.join(root, file) for file in files
                 if os.path.splitext(file)[1] == _py_ext]
                )
        return list
    elif os.path.exists(name):
        # a single file
        return [name]

    return []