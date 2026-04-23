def _find_appropriate_compiler(_config_vars):
    """Find appropriate C compiler for extension module builds"""

    # Issue #13590:
    #    The OSX location for the compiler varies between OSX
    #    (or rather Xcode) releases.  With older releases (up-to 10.5)
    #    the compiler is in /usr/bin, with newer releases the compiler
    #    can only be found inside Xcode.app if the "Command Line Tools"
    #    are not installed.
    #
    #    Furthermore, the compiler that can be used varies between
    #    Xcode releases. Up to Xcode 4 it was possible to use 'gcc-4.2'
    #    as the compiler, after that 'clang' should be used because
    #    gcc-4.2 is either not present, or a copy of 'llvm-gcc' that
    #    miscompiles Python.

    # skip checks if the compiler was overridden with a CC env variable
    if 'CC' in os.environ:
        return _config_vars

    # The CC config var might contain additional arguments.
    # Ignore them while searching.
    cc = oldcc = _config_vars['CC'].split()[0]
    if not _find_executable(cc):
        # Compiler is not found on the shell search PATH.
        # Now search for clang, first on PATH (if the Command LIne
        # Tools have been installed in / or if the user has provided
        # another location via CC).  If not found, try using xcrun
        # to find an uninstalled clang (within a selected Xcode).

        # NOTE: Cannot use subprocess here because of bootstrap
        # issues when building Python itself (and os.popen is
        # implemented on top of subprocess and is therefore not
        # usable as well)

        cc = _find_build_tool('clang')

    elif os.path.basename(cc).startswith('gcc'):
        # Compiler is GCC, check if it is LLVM-GCC
        data = _read_output("'%s' --version"
                             % (cc.replace("'", "'\"'\"'"),))
        if data and 'llvm-gcc' in data:
            # Found LLVM-GCC, fall back to clang
            cc = _find_build_tool('clang')

    if not cc:
        raise SystemError(
               "Cannot locate working compiler")

    if cc != oldcc:
        # Found a replacement compiler.
        # Modify config vars using new compiler, if not already explicitly
        # overridden by an env variable, preserving additional arguments.
        for cv in _COMPILER_CONFIG_VARS:
            if cv in _config_vars and cv not in os.environ:
                cv_split = _config_vars[cv].split()
                cv_split[0] = cc if cv != 'CXX' else cc + '++'
                _save_modified_value(_config_vars, cv, ' '.join(cv_split))

    return _config_vars