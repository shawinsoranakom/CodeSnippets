def missing_compiler_executable(cmd_names=[]):
    """Check if the compiler components used to build the interpreter exist.

    Check for the existence of the compiler executables whose names are listed
    in 'cmd_names' or all the compiler executables when 'cmd_names' is empty
    and return the first missing executable or None when none is found
    missing.

    """
    from setuptools._distutils import ccompiler, sysconfig
    from setuptools import errors
    import shutil

    compiler = ccompiler.new_compiler()
    sysconfig.customize_compiler(compiler)
    if compiler.compiler_type == "msvc":
        # MSVC has no executables, so check whether initialization succeeds
        try:
            compiler.initialize()
        except errors.PlatformError:
            return "msvc"
    for name in compiler.executables:
        if cmd_names and name not in cmd_names:
            continue
        cmd = getattr(compiler, name)
        if cmd_names:
            assert cmd is not None, \
                    "the '%s' executable is not configured" % name
        elif not cmd:
            continue
        if shutil.which(cmd[0]) is None:
            return cmd[0]