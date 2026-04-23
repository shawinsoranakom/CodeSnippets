def get_build_info():
    # Get most important configure and build options as a list of strings.
    # Example: ['debug', 'ASAN+MSAN'] or ['release', 'LTO+PGO'].

    config_args = sysconfig.get_config_var('CONFIG_ARGS') or ''
    cflags = sysconfig.get_config_var('PY_CFLAGS') or ''
    cflags += ' ' + (sysconfig.get_config_var('PY_CFLAGS_NODIST') or '')
    ldflags_nodist = sysconfig.get_config_var('PY_LDFLAGS_NODIST') or ''

    build = []

    # --disable-gil
    if sysconfig.get_config_var('Py_GIL_DISABLED'):
        if not sys.flags.ignore_environment:
            PYTHON_GIL = os.environ.get('PYTHON_GIL', None)
            if PYTHON_GIL:
                PYTHON_GIL = (PYTHON_GIL == '1')
        else:
            PYTHON_GIL = None

        free_threading = "free_threading"
        if PYTHON_GIL is not None:
            free_threading = f"{free_threading} GIL={int(PYTHON_GIL)}"
        build.append(free_threading)

    if hasattr(sys, 'gettotalrefcount'):
        # --with-pydebug
        build.append('debug')

        if '-DNDEBUG' in cflags:
            build.append('without_assert')
    else:
        build.append('release')

        if '--with-assertions' in config_args:
            build.append('with_assert')
        elif '-DNDEBUG' not in cflags:
            build.append('with_assert')

    # --enable-experimental-jit
    if sys._jit.is_available():
        if sys._jit.is_enabled():
            build.append("JIT")
        else:
            build.append("JIT (disabled)")

    # --enable-framework=name
    framework = sysconfig.get_config_var('PYTHONFRAMEWORK')
    if framework:
        build.append(f'framework={framework}')

    # --enable-shared
    shared = int(sysconfig.get_config_var('PY_ENABLE_SHARED') or '0')
    if shared:
        build.append('shared')

    # --with-lto
    optimizations = []
    if '-flto=thin' in ldflags_nodist:
        optimizations.append('ThinLTO')
    elif '-flto' in ldflags_nodist:
        optimizations.append('LTO')

    if support.check_cflags_pgo():
        # PGO (--enable-optimizations)
        optimizations.append('PGO')

    if support.check_bolt_optimized():
        # BOLT (--enable-bolt)
        optimizations.append('BOLT')

    if optimizations:
        build.append('+'.join(optimizations))

    # --with-address-sanitizer
    sanitizers = []
    if support.check_sanitizer(address=True):
        sanitizers.append("ASAN")
    # --with-memory-sanitizer
    if support.check_sanitizer(memory=True):
        sanitizers.append("MSAN")
    # --with-undefined-behavior-sanitizer
    if support.check_sanitizer(ub=True):
        sanitizers.append("UBSAN")
    # --with-thread-sanitizer
    if support.check_sanitizer(thread=True):
        sanitizers.append("TSAN")
    if sanitizers:
        build.append('+'.join(sanitizers))

    # --with-trace-refs
    if hasattr(sys, 'getobjects'):
        build.append("TraceRefs")
    # --enable-pystats
    if hasattr(sys, '_stats_on'):
        build.append("pystats")
    # --with-valgrind
    if sysconfig.get_config_var('WITH_VALGRIND'):
        build.append("valgrind")
    # --with-dtrace
    if sysconfig.get_config_var('WITH_DTRACE'):
        build.append("dtrace")

    return build