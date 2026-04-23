def iter_header_files(filenames=None, *, levels=None):
    if not filenames:
        if levels:
            levels = set(levels)
            if 'private' in levels:
                levels.add('stable')
                levels.add('cpython')
            for level, glob in LEVEL_GLOBS.items():
                if level in levels:
                    yield from expand_filenames([glob])
        else:
            yield from iter_files_by_suffix(INCLUDE_DIRS, ('.h',))
        return

    for filename in filenames:
        orig = filename
        filename = resolve_filename(filename)
        if filename.endswith(os.path.sep):
            yield from iter_files_by_suffix(INCLUDE_DIRS, ('.h',))
        elif filename.endswith('.h'):
            yield filename
        else:
            # XXX Log it and continue instead?
            raise ValueError(f'expected .h file, got {orig!r}')