def _get_variant_and_executable_path():
    """@returns (variant, executable_path)"""
    if getattr(sys, 'frozen', False):
        path = sys.executable

        # py2exe: No longer officially supported, but still identify it to block updates
        if not hasattr(sys, '_MEIPASS'):
            return 'py2exe', path

        # staticx builds: sys.executable returns a /tmp/ path
        # No longer officially supported, but still identify them to block updates
        # Ref: https://staticx.readthedocs.io/en/latest/usage.html#run-time-information
        if static_exe_path := os.getenv('STATICX_PROG_PATH'):
            return 'linux_static_exe', static_exe_path

        # We know it's a PyInstaller bundle, but is it "onedir" or "onefile"?
        if (
            # PyInstaller >= 6.0.0 sets sys._MEIPASS for onedir to its `_internal` subdirectory
            # Ref: https://pyinstaller.org/en/v6.0.0/CHANGES.html#incompatible-changes
            sys._MEIPASS == f'{os.path.dirname(path)}/_internal'
            # compat: PyInstaller < 6.0.0
            or sys._MEIPASS == os.path.dirname(path)
        ):
            suffix = 'dir'
        else:
            suffix = 'exe'

        system_platform = remove_end(sys.platform, '32')

        if system_platform == 'darwin':
            # darwin_legacy_exe is no longer supported, but still identify it to block updates
            machine = '_legacy' if version_tuple(platform.mac_ver()[0]) < (10, 15) else ''
            return f'darwin{machine}_{suffix}', path

        if system_platform == 'linux' and platform.libc_ver()[0] != 'glibc':
            system_platform = 'musllinux'

        machine = f'_{platform.machine().lower()}'
        is_64bits = sys.maxsize > 2**32
        # Ref: https://en.wikipedia.org/wiki/Uname#Examples
        if machine[1:] in ('x86', 'x86_64', 'amd64', 'i386', 'i686'):
            machine = '_x86' if not is_64bits else ''
        # platform.machine() on 32-bit raspbian OS may return 'aarch64', so check "64-bitness"
        # See: https://github.com/yt-dlp/yt-dlp/issues/11813
        elif machine[1:] == 'aarch64' and not is_64bits:
            machine = '_armv7l'

        return f'{system_platform}{machine}_{suffix}', path

    path = os.path.dirname(__file__)
    if isinstance(__loader__, zipimporter):
        return 'zip', os.path.join(path, '..')
    elif (os.path.basename(sys.argv[0]) in ('__main__.py', '-m')
          and os.path.exists(os.path.join(path, '../.git/HEAD'))):
        return 'source', path
    return 'unknown', path