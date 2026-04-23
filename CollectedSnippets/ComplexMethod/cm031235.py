def _init_config_vars():
    global _CONFIG_VARS
    _CONFIG_VARS = {}

    prefix = os.path.normpath(sys.prefix)
    exec_prefix = os.path.normpath(sys.exec_prefix)
    base_prefix = _BASE_PREFIX
    base_exec_prefix = _BASE_EXEC_PREFIX

    try:
        abiflags = sys.abiflags
    except AttributeError:
        abiflags = ''

    if os.name == 'posix':
        _init_posix(_CONFIG_VARS)
        # If we are cross-compiling, load the prefixes from the Makefile instead.
        if '_PYTHON_PROJECT_BASE' in os.environ:
            prefix = _CONFIG_VARS['host_prefix']
            exec_prefix = _CONFIG_VARS['host_exec_prefix']
            base_prefix = _CONFIG_VARS['host_prefix']
            base_exec_prefix = _CONFIG_VARS['host_exec_prefix']
            abiflags = _CONFIG_VARS['ABIFLAGS']

    # Normalized versions of prefix and exec_prefix are handy to have;
    # in fact, these are the standard versions used most places in the
    # Distutils.
    _CONFIG_VARS['prefix'] = prefix
    _CONFIG_VARS['exec_prefix'] = exec_prefix
    _CONFIG_VARS['py_version'] = _PY_VERSION
    _CONFIG_VARS['py_version_short'] = _PY_VERSION_SHORT
    _CONFIG_VARS['py_version_nodot'] = _PY_VERSION_SHORT_NO_DOT
    _CONFIG_VARS['installed_base'] = base_prefix
    _CONFIG_VARS['base'] = prefix
    _CONFIG_VARS['installed_platbase'] = base_exec_prefix
    _CONFIG_VARS['platbase'] = exec_prefix
    _CONFIG_VARS['projectbase'] = _PROJECT_BASE
    _CONFIG_VARS['platlibdir'] = sys.platlibdir
    _CONFIG_VARS['implementation'] = _get_implementation()
    _CONFIG_VARS['implementation_lower'] = _get_implementation().lower()
    _CONFIG_VARS['abiflags'] = abiflags
    try:
        _CONFIG_VARS['py_version_nodot_plat'] = sys.winver.replace('.', '')
    except AttributeError:
        _CONFIG_VARS['py_version_nodot_plat'] = ''

    if os.name == 'nt':
        _init_non_posix(_CONFIG_VARS)
        _CONFIG_VARS['VPATH'] = sys._vpath
    if _HAS_USER_BASE:
        # Setting 'userbase' is done below the call to the
        # init function to enable using 'get_config_var' in
        # the init-function.
        _CONFIG_VARS['userbase'] = _getuserbase()

    # e.g., 't' for free-threaded or '' for default build
    _CONFIG_VARS['abi_thread'] = 't' if _CONFIG_VARS.get('Py_GIL_DISABLED') else ''

    # Always convert srcdir to an absolute path
    srcdir = _CONFIG_VARS.get('srcdir', _PROJECT_BASE)
    if os.name == 'posix':
        if _PYTHON_BUILD:
            # If srcdir is a relative path (typically '.' or '..')
            # then it should be interpreted relative to the directory
            # containing Makefile.
            base = os.path.dirname(get_makefile_filename())
            srcdir = os.path.join(base, srcdir)
        else:
            # srcdir is not meaningful since the installation is
            # spread about the filesystem.  We choose the
            # directory containing the Makefile since we know it
            # exists.
            srcdir = os.path.dirname(get_makefile_filename())
    _CONFIG_VARS['srcdir'] = _safe_realpath(srcdir)

    # OS X platforms require special customization to handle
    # multi-architecture, multi-os-version installers
    if sys.platform == 'darwin':
        import _osx_support
        _osx_support.customize_config_vars(_CONFIG_VARS)

    global _CONFIG_VARS_INITIALIZED
    _CONFIG_VARS_INITIALIZED = True