def get_platform_osx(_config_vars, osname, release, machine):
    """Filter values for get_platform()"""
    # called from get_platform() in sysconfig and distutils.util
    #
    # For our purposes, we'll assume that the system version from
    # distutils' perspective is what MACOSX_DEPLOYMENT_TARGET is set
    # to. This makes the compatibility story a bit more sane because the
    # machine is going to compile and link as if it were
    # MACOSX_DEPLOYMENT_TARGET.

    macver = _config_vars.get('MACOSX_DEPLOYMENT_TARGET', '')
    if macver and '.' not in macver:
        # Ensure that the version includes at least a major
        # and minor version, even if MACOSX_DEPLOYMENT_TARGET
        # is set to a single-label version like "14".
        macver += '.0'
    macrelease = _get_system_version() or macver
    macver = macver or macrelease

    if macver:
        release = macver
        osname = "macosx"

        # Use the original CFLAGS value, if available, so that we
        # return the same machine type for the platform string.
        # Otherwise, distutils may consider this a cross-compiling
        # case and disallow installs.
        cflags = _config_vars.get(_INITPRE+'CFLAGS',
                                    _config_vars.get('CFLAGS', ''))
        if macrelease:
            try:
                macrelease = tuple(int(i) for i in macrelease.split('.')[0:2])
            except ValueError:
                macrelease = (10, 3)
        else:
            # assume no universal support
            macrelease = (10, 3)

        if (macrelease >= (10, 4)) and '-arch' in cflags.strip():
            # The universal build will build fat binaries, but not on
            # systems before 10.4

            machine = 'fat'

            archs = re.findall(r'-arch\s+(\S+)', cflags)
            archs = tuple(sorted(set(archs)))

            if len(archs) == 1:
                machine = archs[0]
            elif archs == ('arm64', 'x86_64'):
                machine = 'universal2'
            elif archs == ('i386', 'ppc'):
                machine = 'fat'
            elif archs == ('i386', 'x86_64'):
                machine = 'intel'
            elif archs == ('i386', 'ppc', 'x86_64'):
                machine = 'fat3'
            elif archs == ('ppc64', 'x86_64'):
                machine = 'fat64'
            elif archs == ('i386', 'ppc', 'ppc64', 'x86_64'):
                machine = 'universal'
            else:
                raise ValueError(
                   "Don't know machine value for archs=%r" % (archs,))

        elif machine == 'i386':
            # On OSX the machine type returned by uname is always the
            # 32-bit variant, even if the executable architecture is
            # the 64-bit variant
            if sys.maxsize >= 2**32:
                machine = 'x86_64'

        elif machine in ('PowerPC', 'Power_Macintosh'):
            # Pick a sane name for the PPC architecture.
            # See 'i386' case
            if sys.maxsize >= 2**32:
                machine = 'ppc64'
            else:
                machine = 'ppc'

    return (osname, release, machine)