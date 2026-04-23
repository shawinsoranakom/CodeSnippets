def get_platform():
    """Return a string that identifies the current platform.

    This is used mainly to distinguish platform-specific build directories and
    platform-specific built distributions.  Typically includes the OS name and
    version and the architecture (as supplied by 'os.uname()'), although the
    exact information included depends on the OS; on Linux, the kernel version
    isn't particularly important.

    Examples of returned values:
       linux-x86_64
       linux-aarch64
       solaris-2.6-sun4u


    Windows:

    - win-amd64 (64-bit Windows on AMD64, aka x86_64, Intel64, and EM64T)
    - win-arm64 (64-bit Windows on ARM64, aka AArch64)
    - win32 (all others - specifically, sys.platform is returned)

    POSIX based OS:

    - linux-x86_64
    - macosx-15.5-arm64
    - macosx-26.0-universal2 (macOS on Apple Silicon or Intel)
    - android-24-arm64_v8a

    For other non-POSIX platforms, currently just returns :data:`sys.platform`."""
    if os.name == 'nt':
        import _sysconfig
        platform = _sysconfig.get_platform()
        if platform:
            return platform
        return sys.platform

    if os.name != "posix" or not hasattr(os, 'uname'):
        # XXX what about the architecture? NT is Intel or Alpha
        return sys.platform

    # Set for cross builds explicitly
    if "_PYTHON_HOST_PLATFORM" in os.environ:
        osname, _, machine = os.environ["_PYTHON_HOST_PLATFORM"].partition('-')
        release = None
    else:
        # Try to distinguish various flavours of Unix
        osname, host, release, version, machine = os.uname()

        # Convert the OS name to lowercase, remove '/' characters, and translate
        # spaces (for "Power Macintosh")
        osname = osname.lower().replace('/', '')
        machine = machine.replace(' ', '_')
        machine = machine.replace('/', '-')

    if osname == "android" or sys.platform == "android":
        osname = "android"
        release = get_config_var("ANDROID_API_LEVEL")

        # Wheel tags use the ABI names from Android's own tools.
        # When Python is running on 32-bit ARM Android on a 64-bit ARM kernel,
        # 'os.uname().machine' is 'armv8l'. Such devices run the same userspace
        # code as 'armv7l' devices.
        # During the build process of the Android testbed when targeting 32-bit ARM,
        # '_PYTHON_HOST_PLATFORM' is 'arm-linux-androideabi', so 'machine' becomes
        # 'arm'.
        machine = {
            "aarch64": "arm64_v8a",
            "arm": "armeabi_v7a",
            "armv7l": "armeabi_v7a",
            "armv8l": "armeabi_v7a",
            "i686": "x86",
            "x86_64": "x86_64",
        }[machine]
    elif osname == "linux":
        # At least on Linux/Intel, 'machine' is the processor --
        # i386, etc.
        # XXX what about Alpha, SPARC, etc?
        return  f"{osname}-{machine}"
    elif osname[:5] == "sunos":
        if release[0] >= "5":           # SunOS 5 == Solaris 2
            osname = "solaris"
            release = f"{int(release[0]) - 3}.{release[2:]}"
            # We can't use "platform.architecture()[0]" because a
            # bootstrap problem. We use a dict to get an error
            # if some suspicious happens.
            bitness = {2147483647:"32bit", 9223372036854775807:"64bit"}
            machine += f".{bitness[sys.maxsize]}"
        # fall through to standard osname-release-machine representation
    elif osname[:3] == "aix":
        from _aix_support import aix_platform
        return aix_platform()
    elif osname[:6] == "cygwin":
        osname = "cygwin"
        import re
        rel_re = re.compile(r'[\d.]+')
        m = rel_re.match(release)
        if m:
            release = m.group()
    elif osname[:6] == "darwin":
        if sys.platform == "ios":
            release = get_config_vars().get("IPHONEOS_DEPLOYMENT_TARGET", "13.0")
            osname = sys.platform
            machine = sys.implementation._multiarch
        else:
            import _osx_support
            osname, release, machine = _osx_support.get_platform_osx(
                                                get_config_vars(),
                                                osname, release, machine)

    return '-'.join(map(str, filter(None, (osname, release, machine))))