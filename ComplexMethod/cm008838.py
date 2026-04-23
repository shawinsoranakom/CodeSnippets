def write_xattr(path, key, value):
    # Windows: Write xattrs to NTFS Alternate Data Streams:
    # http://en.wikipedia.org/wiki/NTFS#Alternate_data_streams_.28ADS.29
    if os.name == 'nt':
        assert ':' not in key
        assert os.path.exists(path)

        try:
            with open(f'{path}:{key}', 'wb') as f:
                f.write(value)
        except OSError as e:
            raise XAttrMetadataError(e.errno, e.strerror)
        return

    # UNIX Method 1. Use os.setxattr/xattrs/pyxattrs modules

    setxattr = None
    if callable(getattr(os, 'setxattr', None)):
        setxattr = os.setxattr
    elif getattr(xattr, '_yt_dlp__identifier', None) == 'pyxattr':
        # Unicode arguments are not supported in pyxattr until version 0.5.0
        # See https://github.com/ytdl-org/youtube-dl/issues/5498
        if version_tuple(xattr.__version__) >= (0, 5, 0):
            setxattr = xattr.set
    elif xattr:
        setxattr = xattr.setxattr

    if setxattr:
        try:
            setxattr(path, key, value)
        except OSError as e:
            raise XAttrMetadataError(e.errno, e.strerror)
        return

    # UNIX Method 2. Use setfattr/xattr executables
    exe = ('setfattr' if check_executable('setfattr', ['--version'])
           else 'xattr' if check_executable('xattr', ['-h']) else None)
    if not exe:
        raise XAttrUnavailableError(
            'Couldn\'t find a tool to set the xattrs. Install either the "xattr" or "pyxattr" Python modules or the '
            + ('"xattr" binary' if sys.platform != 'linux' else 'GNU "attr" package (which contains the "setfattr" tool)'))

    value = value.decode()
    try:
        _, stderr, returncode = Popen.run(
            [exe, '-w', key, value, path] if exe == 'xattr' else [exe, '-n', key, '-v', value, path],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    except OSError as e:
        raise XAttrMetadataError(e.errno, e.strerror)
    if returncode:
        raise XAttrMetadataError(returncode, stderr)