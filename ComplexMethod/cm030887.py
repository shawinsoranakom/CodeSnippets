def collect_windows(info_add):
    if sys.platform != "win32":
        # Code specific to Windows
        return

    # windows.RtlAreLongPathsEnabled: RtlAreLongPathsEnabled()
    # windows.is_admin: IsUserAnAdmin()
    try:
        import ctypes
        if not hasattr(ctypes, 'WinDLL'):
            raise ImportError
    except ImportError:
        pass
    else:
        ntdll = ctypes.WinDLL('ntdll')
        BOOLEAN = ctypes.c_ubyte
        try:
            RtlAreLongPathsEnabled = ntdll.RtlAreLongPathsEnabled
        except AttributeError:
            res = '<function not available>'
        else:
            RtlAreLongPathsEnabled.restype = BOOLEAN
            RtlAreLongPathsEnabled.argtypes = ()
            res = bool(RtlAreLongPathsEnabled())
        info_add('windows.RtlAreLongPathsEnabled', res)

        shell32 = ctypes.windll.shell32
        IsUserAnAdmin = shell32.IsUserAnAdmin
        IsUserAnAdmin.restype = BOOLEAN
        IsUserAnAdmin.argtypes = ()
        info_add('windows.is_admin', IsUserAnAdmin())

    try:
        import _winapi
    except ImportError:
        pass
    else:
        try:
            dll_path = _winapi.GetModuleFileName(sys.dllhandle)
            info_add('windows.dll_path', dll_path)
        except AttributeError:
            pass

        call_func(info_add, 'windows.ansi_code_page', _winapi, 'GetACP')
        call_func(info_add, 'windows.oem_code_page', _winapi, 'GetOEMCP')

    # windows.version_caption: "wmic os get Caption,Version /value" command
    import subprocess
    try:
        # When wmic.exe output is redirected to a pipe,
        # it uses the OEM code page
        proc = subprocess.Popen(["wmic", "os", "get", "Caption,Version", "/value"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                encoding="oem",
                                text=True)
        output, stderr = proc.communicate()
        if proc.returncode:
            output = ""
    except OSError:
        pass
    else:
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('Caption='):
                line = line.removeprefix('Caption=').strip()
                if line:
                    info_add('windows.version_caption', line)
            elif line.startswith('Version='):
                line = line.removeprefix('Version=').strip()
                if line:
                    info_add('windows.version', line)

    # windows.ver: "ver" command
    try:
        proc = subprocess.Popen(["ver"], shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        output = proc.communicate()[0]
        if proc.returncode == 0xc0000142:
            return
        if proc.returncode:
            output = ""
    except OSError:
        return
    else:
        output = output.strip()
        line = output.splitlines()[0]
        if line:
            info_add('windows.ver', line)

    # windows.developer_mode: get AllowDevelopmentWithoutDevLicense registry
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock")
        subkey = "AllowDevelopmentWithoutDevLicense"
        try:
            value, value_type = winreg.QueryValueEx(key, subkey)
        finally:
            winreg.CloseKey(key)
    except OSError:
        pass
    else:
        info_add('windows.developer_mode', "enabled" if value else "disabled")