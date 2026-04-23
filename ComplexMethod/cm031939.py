def get_host_platform():
    """Return a string that identifies the current platform.  This is used mainly to
    distinguish platform-specific build directories and platform-specific built
    distributions.  Typically includes the OS name and version and the
    architecture (as supplied by 'os.uname()'), although the exact information
    included depends on the OS; eg. on Linux, the kernel version isn't
    particularly important.

    Examples of returned values:
       linux-x86_64
       linux-aarch64
       solaris-2.6-sun4u

    Windows will return one of:
       win-amd64 (64bit Windows on AMD64 (aka x86_64, Intel64, EM64T, etc)
       win32 (all others - specifically, sys.platform is returned)

    For other non-POSIX platforms, currently just returns 'sys.platform'.

    """
    if os.name == 'nt':
        if 'amd64' in sys.version.lower():
            return 'win-amd64'
        if '(arm)' in sys.version.lower():
            return 'win-arm32'
        if '(arm64)' in sys.version.lower():
            return 'win-arm64'
        return sys.platform

    # Set for cross builds explicitly
    if "_PYTHON_HOST_PLATFORM" in os.environ:
        return os.environ["_PYTHON_HOST_PLATFORM"]

    if os.name != "posix" or not hasattr(os, 'uname'):
        # XXX what about the architecture? NT is Intel or Alpha,
        # Mac OS is M68k or PPC, etc.
        return sys.platform

    # Try to distinguish various flavours of Unix

    (osname, host, release, version, machine) = os.uname()

    # Convert the OS name to lowercase, remove '/' characters, and translate
    # spaces (for "Power Macintosh")
    osname = osname.lower().replace('/', '')
    machine = machine.replace(' ', '_')
    machine = machine.replace('/', '-')

    if osname[:5] == "linux":
        # At least on Linux/Intel, 'machine' is the processor --
        # i386, etc.
        # XXX what about Alpha, SPARC, etc?
        return  "%s-%s" % (osname, machine)
    elif osname[:5] == "sunos":
        if release[0] >= "5":           # SunOS 5 == Solaris 2
            osname = "solaris"
            release = "%d.%s" % (int(release[0]) - 3, release[2:])
            # We can't use "platform.architecture()[0]" because a
            # bootstrap problem. We use a dict to get an error
            # if some suspicious happens.
            bitness = {2147483647:"32bit", 9223372036854775807:"64bit"}
            machine += ".%s" % bitness[sys.maxsize]
        # fall through to standard osname-release-machine representation
    elif osname[:3] == "aix":
        from _aix_support import aix_platform
        return aix_platform()
    elif osname[:6] == "cygwin":
        osname = "cygwin"
        rel_re = re.compile (r'[\d.]+', re.ASCII)
        m = rel_re.match(release)
        if m:
            release = m.group()
    elif osname[:6] == "darwin":
        import _osx_support, sysconfig
        osname, release, machine = _osx_support.get_platform_osx(
                                        sysconfig.get_config_vars(),
                                        osname, release, machine)

    return "%s-%s-%s" % (osname, release, machine)