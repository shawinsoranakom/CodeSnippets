def collect_sysconfig(info_add):
    import sysconfig

    info_add('sysconfig.is_python_build', sysconfig.is_python_build())

    for name in (
        'ABIFLAGS',
        'ANDROID_API_LEVEL',
        'CC',
        'CCSHARED',
        'CFLAGS',
        'CFLAGSFORSHARED',
        'CONFIG_ARGS',
        'HOSTRUNNER',
        'HOST_GNU_TYPE',
        'MACHDEP',
        'MULTIARCH',
        'OPT',
        'PGO_PROF_USE_FLAG',
        'PY_CFLAGS',
        'PY_CFLAGS_NODIST',
        'PY_CORE_LDFLAGS',
        'PY_CORE_EXE_LDFLAGS',
        'PY_LDFLAGS',
        'PY_LDFLAGS_NODIST',
        'PY_STDMODULE_CFLAGS',
        'Py_DEBUG',
        'Py_ENABLE_SHARED',
        'Py_GIL_DISABLED',
        'Py_REMOTE_DEBUG',
        'SHELL',
        'SOABI',
        'TEST_MODULES',
        'VAPTH',
        'abs_builddir',
        'abs_srcdir',
        'prefix',
        'srcdir',
    ):
        value = sysconfig.get_config_var(name)
        if name == 'ANDROID_API_LEVEL' and not value:
            # skip ANDROID_API_LEVEL=0
            continue
        value = normalize_text(value)
        info_add('sysconfig[%s]' % name, value)

    PY_CFLAGS = sysconfig.get_config_var('PY_CFLAGS')
    NDEBUG = (PY_CFLAGS and '-DNDEBUG' in PY_CFLAGS)
    if NDEBUG:
        text = 'ignore assertions (macro defined)'
    else:
        text= 'build assertions (macro not defined)'
    info_add('build.NDEBUG',text)

    for name in (
        'WITH_DOC_STRINGS',
        'WITH_DTRACE',
        'WITH_MIMALLOC',
        'WITH_PYMALLOC',
        'WITH_VALGRIND',
    ):
        value = sysconfig.get_config_var(name)
        if value:
            text = 'Yes'
        else:
            text = 'No'
        info_add(f'build.{name}', text)