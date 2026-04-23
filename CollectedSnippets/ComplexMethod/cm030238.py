def _win32_ver(version, csd, ptype):
    # Try using WMI first, as this is the canonical source of data
    try:
        (version, product_type, ptype, spmajor, spminor)  = _wmi_query(
            'OS',
            'Version',
            'ProductType',
            'BuildType',
            'ServicePackMajorVersion',
            'ServicePackMinorVersion',
        )
        is_client = (int(product_type) == 1)
        if spminor and spminor != '0':
            csd = f'SP{spmajor}.{spminor}'
        else:
            csd = f'SP{spmajor}'
        return version, csd, ptype, is_client
    except OSError:
        pass

    # Fall back to a combination of sys.getwindowsversion and "ver"
    try:
        from sys import getwindowsversion
    except ImportError:
        return version, csd, ptype, True

    winver = getwindowsversion()
    is_client = (getattr(winver, 'product_type', 1) == 1)
    try:
        version = _syscmd_ver()[2]
        major, minor, build = map(int, version.split('.'))
    except ValueError:
        major, minor, build = winver.platform_version or winver[:3]
        version = '{0}.{1}.{2}'.format(major, minor, build)

    # getwindowsversion() reflect the compatibility mode Python is
    # running under, and so the service pack value is only going to be
    # valid if the versions match.
    if winver[:2] == (major, minor):
        try:
            csd = 'SP{}'.format(winver.service_pack_major)
        except AttributeError:
            if csd[:13] == 'Service Pack ':
                csd = 'SP' + csd[13:]

    try:
        import winreg
    except ImportError:
        pass
    else:
        try:
            cvkey = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
            with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, cvkey) as key:
                ptype = winreg.QueryValueEx(key, 'CurrentType')[0]
        except OSError:
            pass

    return version, csd, ptype, is_client