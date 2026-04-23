def uname():

    """ Fairly portable uname interface. Returns a tuple
        of strings (system, node, release, version, machine, processor)
        identifying the underlying platform.

        Note that unlike the os.uname function this also returns
        possible processor information as an additional tuple entry.

        Entries which cannot be determined are set to ''.

    """
    global _uname_cache

    if _uname_cache is not None:
        return _uname_cache

    # Get some infos from the builtin os.uname API...
    try:
        system, node, release, version, machine = infos = os.uname()
    except AttributeError:
        system = sys.platform
        node = _node()
        release = version = machine = ''
        infos = ()

    if not any(infos):
        # uname is not available

        # Try win32_ver() on win32 platforms
        if system == 'win32':
            release, version, csd, ptype = win32_ver()
            machine = machine or _get_machine_win32()

        # Try the 'ver' system command available on some
        # platforms
        if not (release and version):
            system, release, version = _syscmd_ver(system)
            # Normalize system to what win32_ver() normally returns
            # (_syscmd_ver() tends to return the vendor name as well)
            if system == 'Microsoft Windows':
                system = 'Windows'
            elif system == 'Microsoft' and release == 'Windows':
                # Under Windows Vista and Windows Server 2008,
                # Microsoft changed the output of the ver command. The
                # release is no longer printed.  This causes the
                # system and release to be misidentified.
                system = 'Windows'
                if '6.0' == version[:3]:
                    release = 'Vista'
                else:
                    release = ''

        # In case we still don't know anything useful, we'll try to
        # help ourselves
        if system in ('win32', 'win16'):
            if not version:
                if system == 'win32':
                    version = '32bit'
                else:
                    version = '16bit'
            system = 'Windows'

    # System specific extensions
    if system == 'OpenVMS':
        # OpenVMS seems to have release and version mixed up
        if not release or release == '0':
            release = version
            version = ''

    #  normalize name
    if system == 'Microsoft' and release == 'Windows':
        system = 'Windows'
        release = 'Vista'

    # On Android, return the name and version of the OS rather than the kernel.
    if sys.platform == 'android':
        system = 'Android'
        release = android_ver().release

    # Normalize responses on iOS
    if sys.platform == 'ios':
        system, release, _, _ = ios_ver()

    vals = system, node, release, version, machine
    # Replace 'unknown' values with the more portable ''
    _uname_cache = uname_result(*map(_unknown_as_blank, vals))
    return _uname_cache