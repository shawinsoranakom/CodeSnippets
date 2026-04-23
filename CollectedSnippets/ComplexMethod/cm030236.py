def libc_ver(executable=None, lib='', version='', chunksize=16384):

    """ Tries to determine the libc version that the file executable
        (which defaults to the Python interpreter) is linked against.

        Returns a tuple of strings (lib,version) which default to the
        given parameters in case the lookup fails.

        Note that the function has intimate knowledge of how different
        libc versions add symbols to the executable and thus is probably
        only usable for executables compiled using gcc.

        The file is read and scanned in chunks of chunksize bytes.

    """
    if not executable:
        if sys.platform == "emscripten":
            # Emscripten's os.confstr reports that it is glibc, so special case
            # it.
            ver = ".".join(str(x) for x in sys._emscripten_info.emscripten_version)
            return ("emscripten", ver)
        try:
            ver = os.confstr('CS_GNU_LIBC_VERSION')
            # parse 'glibc 2.28' as ('glibc', '2.28')
            parts = ver.split(maxsplit=1)
            if len(parts) == 2:
                return tuple(parts)
        except (AttributeError, ValueError, OSError):
            # os.confstr() or CS_GNU_LIBC_VERSION value not available
            pass

        executable = sys.executable

        if not executable:
            # sys.executable is not set.
            return lib, version

    libc_search = re.compile(br"""
          (__libc_init)
        | (GLIBC_([0-9.]+))
        | (libc(_\w+)?\.so(?:\.(\d[0-9.]*))?)
        | (musl-([0-9.]+))
        | ((?:libc\.|ld-)musl(?:-\w+)?.so(?:\.(\d[0-9.]*))?)
        """,
        re.ASCII | re.VERBOSE)

    V = _comparable_version
    # We use os.path.realpath()
    # here to work around problems with Cygwin not being
    # able to open symlinks for reading
    executable = os.path.realpath(executable)
    ver = None
    with open(executable, 'rb') as f:
        binary = f.read(chunksize)
        pos = 0
        while pos < len(binary):
            if b'libc' in binary or b'GLIBC' in binary or b'musl' in binary:
                m = libc_search.search(binary, pos)
            else:
                m = None
            if not m or m.end() == len(binary):
                chunk = f.read(chunksize)
                if chunk:
                    binary = binary[max(pos, len(binary) - 1000):] + chunk
                    pos = 0
                    continue
                if not m:
                    break
            decoded_groups = [s.decode('latin1') if s is not None else s
                              for s in m.groups()]
            (libcinit, glibc, glibcversion, so, threads, soversion,
             musl, muslversion, musl_so, musl_sover) = decoded_groups
            if libcinit and not lib:
                lib = 'libc'
            elif glibc:
                if lib != 'glibc':
                    lib = 'glibc'
                    ver = glibcversion
                elif V(glibcversion) > V(ver):
                    ver = glibcversion
            elif so:
                if lib not in ('glibc', 'musl'):
                    lib = 'libc'
                    if soversion and (not ver or V(soversion) > V(ver)):
                        ver = soversion
                    if threads and ver[-len(threads):] != threads:
                        ver = ver + threads
            elif musl:
                lib = 'musl'
                if not ver or V(muslversion) > V(ver):
                    ver = muslversion
            elif musl_so:
                lib = 'musl'
                if musl_sover and (not ver or V(musl_sover) > V(ver)):
                    ver = musl_sover
            pos = m.end()
    return lib, version if ver is None else ver