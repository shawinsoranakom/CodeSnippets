def _module_relative_path(module, test_path):
    if not inspect.ismodule(module):
        raise TypeError('Expected a module: %r' % module)
    if test_path.startswith('/'):
        raise ValueError('Module-relative files may not have absolute paths')

    # Normalize the path. On Windows, replace "/" with "\".
    test_path = os.path.join(*(test_path.split('/')))

    # Find the base directory for the path.
    if hasattr(module, '__file__'):
        # A normal module/package
        basedir = os.path.split(module.__file__)[0]
    elif module.__name__ == '__main__':
        # An interactive session.
        if len(sys.argv)>0 and sys.argv[0] != '':
            basedir = os.path.split(sys.argv[0])[0]
        else:
            basedir = os.curdir
    else:
        if hasattr(module, '__path__'):
            for directory in module.__path__:
                fullpath = os.path.join(directory, test_path)
                if os.path.exists(fullpath):
                    return fullpath

        # A module w/o __file__ (this includes builtins)
        raise ValueError("Can't resolve paths relative to the module "
                         "%r (it has no __file__)"
                         % module.__name__)

    # Combine the base directory and the test path.
    return os.path.join(basedir, test_path)