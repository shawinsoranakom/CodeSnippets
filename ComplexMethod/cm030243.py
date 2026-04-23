def platform(aliased=False, terse=False):

    """ Returns a single string identifying the underlying platform
        with as much useful information as possible (but no more :).

        The output is intended to be human readable rather than
        machine parseable. It may look different on different
        platforms and this is intended.

        If "aliased" is true, the function will use aliases for
        various platforms that report system names which differ from
        their common names, e.g. SunOS will be reported as
        Solaris. The system_alias() function is used to implement
        this.

        Setting terse to true causes the function to return only the
        absolute minimum information needed to identify the platform.

    """
    result = _platform_cache.get((aliased, terse), None)
    if result is not None:
        return result

    # Get uname information and then apply platform specific cosmetics
    # to it...
    system, node, release, version, machine, processor = uname()
    if machine == processor:
        processor = ''
    if aliased:
        system, release, version = system_alias(system, release, version)

    if system == 'Darwin':
        # macOS and iOS both report as a "Darwin" kernel
        if sys.platform == "ios":
            system, release, _, _ = ios_ver()
        else:
            macos_release = mac_ver()[0]
            if macos_release:
                system = 'macOS'
                release = macos_release

    if system == 'Windows':
        # MS platforms
        rel, vers, csd, ptype = win32_ver(version)
        if terse:
            platform = _platform(system, release)
        else:
            platform = _platform(system, release, version, csd)

    elif system == 'Linux':
        # check for libc vs. glibc
        libcname, libcversion = libc_ver()
        platform = _platform(system, release, machine, processor,
                             'with',
                             libcname+libcversion)

    else:
        # Generic handler
        if terse:
            platform = _platform(system, release)
        else:
            bits, linkage = architecture(sys.executable)
            platform = _platform(system, release, machine,
                                 processor, bits, linkage)

    _platform_cache[(aliased, terse)] = platform
    return platform