def create_modules(*names):
    """Temporarily create each named module with an attribute (named 'attr')
    that contains the name passed into the context manager that caused the
    creation of the module.

    All files are created in a temporary directory returned by
    tempfile.mkdtemp(). This directory is inserted at the beginning of
    sys.path. When the context manager exits all created files (source and
    bytecode) are explicitly deleted.

    No magic is performed when creating packages! This means that if you create
    a module within a package you must also create the package's __init__ as
    well.

    """
    source = 'attr = {0!r}'
    created_paths = []
    mapping = {}
    state_manager = None
    uncache_manager = None
    try:
        temp_dir = tempfile.mkdtemp()
        mapping['.root'] = temp_dir
        import_names = set()
        for name in names:
            if not name.endswith('__init__'):
                import_name = name
            else:
                import_name = name[:-len('.__init__')]
            import_names.add(import_name)
            if import_name in sys.modules:
                del sys.modules[import_name]
            name_parts = name.split('.')
            file_path = temp_dir
            for directory in name_parts[:-1]:
                file_path = os.path.join(file_path, directory)
                if not os.path.exists(file_path):
                    os.mkdir(file_path)
                    created_paths.append(file_path)
            file_path = os.path.join(file_path, name_parts[-1] + '.py')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(source.format(name))
            created_paths.append(file_path)
            mapping[name] = file_path
        uncache_manager = uncache(*import_names)
        uncache_manager.__enter__()
        state_manager = import_state(path=[temp_dir])
        state_manager.__enter__()
        yield mapping
    finally:
        if state_manager is not None:
            state_manager.__exit__(None, None, None)
        if uncache_manager is not None:
            uncache_manager.__exit__(None, None, None)
        os_helper.rmtree(temp_dir)