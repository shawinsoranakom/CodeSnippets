def main():
    cppflags = list(CPPFLAGS)
    std = os.environ.get("CPYTHON_TEST_CPP_STD", "")
    module_name = os.environ["CPYTHON_TEST_EXT_NAME"]
    limited = bool(os.environ.get("CPYTHON_TEST_LIMITED", ""))
    internal = bool(int(os.environ.get("TEST_INTERNAL_C_API", "0")))

    cppflags = list(CPPFLAGS)
    cppflags.append(f'-DMODULE_NAME={module_name}')

    # Add -std=STD or /std:STD (MSVC) compiler flag
    if std:
        if support.MS_WINDOWS:
            cppflags.append(f'/std:{std}')
        else:
            cppflags.append(f'-std={std}')

        if limited or (std != 'c++03') and not internal:
            # See CPPFLAGS_PEDANTIC docstring
            cppflags.extend(CPPFLAGS_PEDANTIC)

    # gh-105776: When "gcc -std=11" is used as the C++ compiler, -std=c11
    # option emits a C++ compiler warning. Remove "-std11" option from the
    # CC command.
    cmd = (sysconfig.get_config_var('CC') or '')
    if cmd is not None:
        if support.MS_WINDOWS:
            std_prefix = '/std'
        else:
            std_prefix = '-std'
        cmd = shlex.split(cmd)
        cmd = [arg for arg in cmd if not arg.startswith(std_prefix)]
        cmd = shlex.join(cmd)
        # CC env var overrides sysconfig CC variable in setuptools
        os.environ['CC'] = cmd

    # Define Py_LIMITED_API macro
    if limited:
        version = sys.hexversion
        cppflags.append(f'-DPy_LIMITED_API={version:#x}')

    if internal:
        cppflags.append('-DTEST_INTERNAL_C_API=1')

    extra_cflags = os.environ.get("CPYTHON_TEST_EXTRA_CFLAGS", "")
    if extra_cflags:
        cppflags.extend(shlex.split(extra_cflags))

    # On Windows, add PCbuild\amd64\ to include and library directories
    include_dirs = []
    library_dirs = []
    if support.MS_WINDOWS:
        srcdir = sysconfig.get_config_var('srcdir')
        machine = platform.uname().machine
        pcbuild = os.path.join(srcdir, 'PCbuild', machine)
        if os.path.exists(pcbuild):
            # pyconfig.h is generated in PCbuild\amd64\
            include_dirs.append(pcbuild)
            # python313.lib is generated in PCbuild\amd64\
            library_dirs.append(pcbuild)
            print(f"Add PCbuild directory: {pcbuild}")

    # Display information to help debugging
    for env_name in ('CC', 'CXX', 'CFLAGS', 'CPPFLAGS', 'CXXFLAGS'):
        if env_name in os.environ:
            print(f"{env_name} env var: {os.environ[env_name]!r}")
        else:
            print(f"{env_name} env var: <missing>")
    print(f"extra_compile_args: {cppflags!r}")

    ext = Extension(
        module_name,
        sources=[SOURCE],
        language='c++',
        extra_compile_args=cppflags,
        include_dirs=include_dirs,
        library_dirs=library_dirs)
    setup(name=f'internal_{module_name}',
          version='0.0',
          ext_modules=[ext])