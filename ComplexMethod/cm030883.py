def collect_sys(info_add):
    attributes = (
        '_emscripten_info',
        '_framework',
        'abiflags',
        'api_version',
        'builtin_module_names',
        'byteorder',
        'dont_write_bytecode',
        'executable',
        'flags',
        'float_info',
        'float_repr_style',
        'hash_info',
        'hexversion',
        'implementation',
        'int_info',
        'maxsize',
        'maxunicode',
        'path',
        'platform',
        'platlibdir',
        'prefix',
        'thread_info',
        'version',
        'version_info',
        'winver',
    )
    copy_attributes(info_add, sys, 'sys.%s', attributes)

    for func in (
        '_is_gil_enabled',
        'getandroidapilevel',
        'getrecursionlimit',
        'getwindowsversion',
    ):
        call_func(info_add, f'sys.{func}', sys, func)

    encoding = sys.getfilesystemencoding()
    if hasattr(sys, 'getfilesystemencodeerrors'):
        encoding = '%s/%s' % (encoding, sys.getfilesystemencodeerrors())
    info_add('sys.filesystem_encoding', encoding)

    for name in ('stdin', 'stdout', 'stderr'):
        stream = getattr(sys, name)
        if stream is None:
            continue
        encoding = getattr(stream, 'encoding', None)
        if not encoding:
            continue
        errors = getattr(stream, 'errors', None)
        if errors:
            encoding = '%s/%s' % (encoding, errors)
        info_add('sys.%s.encoding' % name, encoding)

    # Were we compiled --with-pydebug?
    Py_DEBUG = hasattr(sys, 'gettotalrefcount')
    if Py_DEBUG:
        text = 'Yes (sys.gettotalrefcount() present)'
    else:
        text = 'No (sys.gettotalrefcount() missing)'
    info_add('build.Py_DEBUG', text)

    # Were we compiled --with-trace-refs?
    Py_TRACE_REFS = hasattr(sys, 'getobjects')
    if Py_TRACE_REFS:
        text = 'Yes (sys.getobjects() present)'
    else:
        text = 'No (sys.getobjects() missing)'
    info_add('build.Py_TRACE_REFS', text)

    info_add('sys.is_remote_debug_enabled', sys.is_remote_debug_enabled())