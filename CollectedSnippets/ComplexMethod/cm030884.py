def collect_os(info_add):
    import os

    def format_attr(attr, value):
        if attr in ('supports_follow_symlinks', 'supports_fd',
                    'supports_effective_ids'):
            return str(sorted(func.__name__ for func in value))
        else:
            return value

    attributes = (
        'name',
        'supports_bytes_environ',
        'supports_effective_ids',
        'supports_fd',
        'supports_follow_symlinks',
    )
    copy_attributes(info_add, os, 'os.%s', attributes, formatter=format_attr)

    for func in (
        'cpu_count',
        'getcwd',
        'getegid',
        'geteuid',
        'getgid',
        'getloadavg',
        'getresgid',
        'getresuid',
        'getuid',
        'process_cpu_count',
        'uname',
    ):
        call_func(info_add, 'os.%s' % func, os, func)

    def format_groups(groups):
        return ', '.join(map(str, groups))

    call_func(info_add, 'os.getgroups', os, 'getgroups', formatter=format_groups)

    if hasattr(os, 'getlogin'):
        try:
            login = os.getlogin()
        except OSError:
            # getlogin() fails with "OSError: [Errno 25] Inappropriate ioctl
            # for device" on Travis CI
            pass
        else:
            info_add("os.login", login)

    # Environment variables used by the stdlib and tests. Don't log the full
    # environment: filter to list to not leak sensitive information.
    #
    # HTTP_PROXY is not logged because it can contain a password.
    ENV_VARS = frozenset((
        "APPDATA",
        "AR",
        "ARCHFLAGS",
        "ARFLAGS",
        "AUDIODEV",
        "BUILDPYTHON",
        "CC",
        "CFLAGS",
        "COLUMNS",
        "COMPUTERNAME",
        "COMSPEC",
        "CPP",
        "CPPFLAGS",
        "DISPLAY",
        "DISTUTILS_DEBUG",
        "DISTUTILS_USE_SDK",
        "DYLD_LIBRARY_PATH",
        "ENSUREPIP_OPTIONS",
        "FORCE_COLOR",
        "GITHUB_ACTIONS",
        "HISTORY_FILE",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "IDLESTARTUP",
        "IPHONEOS_DEPLOYMENT_TARGET",
        "LANG",
        "LDFLAGS",
        "LDSHARED",
        "LD_LIBRARY_PATH",
        "LINES",
        "MACOSX_DEPLOYMENT_TARGET",
        "MAILCAPS",
        "MAKEFLAGS",
        "MIXERDEV",
        "MSSDK",
        "NO_COLOR",
        "PATH",
        "PATHEXT",
        "PIP_CONFIG_FILE",
        "PLAT",
        "POSIXLY_CORRECT",
        "PYTHON_COLORS",
        "PY_SAX_PARSER",
        "ProgramFiles",
        "ProgramFiles(x86)",
        "RUNNING_ON_VALGRIND",
        "SDK_TOOLS_BIN",
        "SERVER_SOFTWARE",
        "SHELL",
        "SOURCE_DATE_EPOCH",
        "SYSTEMROOT",
        "TEMP",
        "TERM",
        "TILE_LIBRARY",
        "TMP",
        "TMPDIR",
        "TRAVIS",
        "TZ",
        "USERPROFILE",
        "VIRTUAL_ENV",
        "WAYLAND_DISPLAY",
        "WINDIR",
        "_PYTHON_HOSTRUNNER",
        "_PYTHON_HOST_PLATFORM",
        "_PYTHON_PROJECT_BASE",
        "_PYTHON_SYSCONFIGDATA_NAME",
        "_PYTHON_SYSCONFIGDATA_PATH",
        "__PYVENV_LAUNCHER__",

        # Sanitizer options
        "ASAN_OPTIONS",
        "LSAN_OPTIONS",
        "MSAN_OPTIONS",
        "TSAN_OPTIONS",
        "UBSAN_OPTIONS",
    ))
    for name, value in os.environ.items():
        uname = name.upper()
        if (uname in ENV_VARS
           # Copy PYTHON* variables like PYTHONPATH
           # Copy LC_* variables like LC_ALL
           or uname.startswith(("PYTHON", "LC_"))
           # Visual Studio: VS140COMNTOOLS
           or (uname.startswith("VS") and uname.endswith("COMNTOOLS"))):
            info_add('os.environ[%s]' % name, value)

    if hasattr(os, 'umask'):
        mask = os.umask(0)
        os.umask(mask)
        info_add("os.umask", '0o%03o' % mask)