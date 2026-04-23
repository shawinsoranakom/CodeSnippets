def main():
    std = os.environ.get("CPYTHON_TEST_STD", "")
    module_name = os.environ["CPYTHON_TEST_EXT_NAME"]
    limited = bool(os.environ.get("CPYTHON_TEST_LIMITED", ""))
    abi3t = bool(os.environ.get("CPYTHON_TEST_ABI3T", ""))
    internal = bool(int(os.environ.get("TEST_INTERNAL_C_API", "0")))

    sources = [SOURCE]

    if not internal:
        cflags = list(PUBLIC_CFLAGS)
    else:
        cflags = list(INTERNAL_CFLAGS)
    cflags.append(f'-DMODULE_NAME={module_name}')

    # Add -std=STD or /std:STD (MSVC) compiler flag
    if std:
        if support.MS_WINDOWS:
            cflags.append(f'/std:{std}')
        else:
            cflags.append(f'-std={std}')

    # Remove existing -std or /std options from CC command line.
    # Python adds -std=c11 option.
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

    # Define opt-in macros
    if limited:
        cflags.append(f'-DPy_LIMITED_API={sys.hexversion:#x}')

    if abi3t:
        cflags.append(f'-DPy_TARGET_ABI3T={sys.hexversion:#x}')

    if internal:
        cflags.append('-DTEST_INTERNAL_C_API=1')

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
    for env_name in ('CC', 'CFLAGS', 'CPPFLAGS'):
        if env_name in os.environ:
            print(f"{env_name} env var: {os.environ[env_name]!r}")
        else:
            print(f"{env_name} env var: <missing>")
    print(f"extra_compile_args: {cflags!r}")

    ext = Extension(
        module_name,
        sources=sources,
        extra_compile_args=cflags,
        include_dirs=include_dirs,
        library_dirs=library_dirs)
    setup(name=f'internal_{module_name}',
          version='0.0',
          ext_modules=[ext])