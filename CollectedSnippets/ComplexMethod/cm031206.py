def cache_from_source(path, *, optimization=None):
    """Given the path to a .py file, return the path to its .pyc file.

    The .py file does not need to exist; this simply returns the path to the
    .pyc file calculated as if the .py file were imported.

    The 'optimization' parameter controls the presumed optimization level of
    the bytecode file. If 'optimization' is not None, the string representation
    of the argument is taken and verified to be alphanumeric (else ValueError
    is raised).

    If sys.implementation.cache_tag is None then NotImplementedError is raised.

    """
    path = _os.fspath(path)
    head, tail = _path_split(path)
    base, sep, rest = tail.rpartition('.')
    tag = sys.implementation.cache_tag
    if tag is None:
        raise NotImplementedError('sys.implementation.cache_tag is None')
    almost_filename = ''.join([(base if base else rest), sep, tag])
    if optimization is None:
        if sys.flags.optimize == 0:
            optimization = ''
        else:
            optimization = sys.flags.optimize
    optimization = str(optimization)
    if optimization != '':
        if not optimization.isalnum():
            raise ValueError(f'{optimization!r} is not alphanumeric')
        almost_filename = f'{almost_filename}.{_OPT}{optimization}'
    filename = almost_filename + BYTECODE_SUFFIXES[0]
    if sys.pycache_prefix is not None:
        # We need an absolute path to the py file to avoid the possibility of
        # collisions within sys.pycache_prefix, if someone has two different
        # `foo/bar.py` on their system and they import both of them using the
        # same sys.pycache_prefix. Let's say sys.pycache_prefix is
        # `C:\Bytecode`; the idea here is that if we get `Foo\Bar`, we first
        # make it absolute (`C:\Somewhere\Foo\Bar`), then make it root-relative
        # (`Somewhere\Foo\Bar`), so we end up placing the bytecode file in an
        # unambiguous `C:\Bytecode\Somewhere\Foo\Bar\`.
        head = _path_abspath(head)

        # Strip initial drive from a Windows path. We know we have an absolute
        # path here, so the second part of the check rules out a POSIX path that
        # happens to contain a colon at the second character.
        # Slicing avoids issues with an empty (or short) `head`.
        if head[1:2] == ':' and head[0:1] not in path_separators:
            head = head[2:]

        # Strip initial path separator from `head` to complete the conversion
        # back to a root-relative path before joining.
        return _path_join(
            sys.pycache_prefix,
            head.lstrip(path_separators),
            filename,
        )
    return _path_join(head, _PYCACHE, filename)