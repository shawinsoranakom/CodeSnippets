def _is_gui_available():
    if hasattr(_is_gui_available, 'result'):
        return _is_gui_available.result
    import platform
    reason = None
    if sys.platform.startswith('win') and platform.win32_is_iot():
        reason = "gui is not available on Windows IoT Core"
    elif sys.platform.startswith('win'):
        # if Python is running as a service (such as the buildbot service),
        # gui interaction may be disallowed
        import ctypes
        import ctypes.wintypes
        UOI_FLAGS = 1
        WSF_VISIBLE = 0x0001
        class USEROBJECTFLAGS(ctypes.Structure):
            _fields_ = [("fInherit", ctypes.wintypes.BOOL),
                        ("fReserved", ctypes.wintypes.BOOL),
                        ("dwFlags", ctypes.wintypes.DWORD)]
        dll = ctypes.windll.user32
        h = dll.GetProcessWindowStation()
        if not h:
            raise ctypes.WinError()
        uof = USEROBJECTFLAGS()
        needed = ctypes.wintypes.DWORD()
        res = dll.GetUserObjectInformationW(h,
            UOI_FLAGS,
            ctypes.byref(uof),
            ctypes.sizeof(uof),
            ctypes.byref(needed))
        if not res:
            raise ctypes.WinError()
        if not bool(uof.dwFlags & WSF_VISIBLE):
            reason = "gui not available (WSF_VISIBLE flag not set)"
    elif sys.platform == 'darwin':
        # The Aqua Tk implementations on OS X can abort the process if
        # being called in an environment where a window server connection
        # cannot be made, for instance when invoked by a buildbot or ssh
        # process not running under the same user id as the current console
        # user.  To avoid that, raise an exception if the window manager
        # connection is not available.
        import subprocess
        try:
            rc = subprocess.run(["launchctl", "managername"],
                                capture_output=True, check=True)
            managername = rc.stdout.decode("utf-8").strip()
        except subprocess.CalledProcessError:
            reason = "unable to detect macOS launchd job manager"
        else:
            if managername != "Aqua":
                reason = f"{managername=} -- can only run in a macOS GUI session"

    # check on every platform whether tkinter can actually do anything
    if not reason:
        try:
            from tkinter import Tk
            root = Tk()
            root.withdraw()
            root.update()
            root.destroy()
        except Exception as e:
            err_string = str(e)
            if len(err_string) > 50:
                err_string = err_string[:50] + ' [...]'
            reason = 'Tk unavailable due to {}: {}'.format(type(e).__name__,
                                                           err_string)

    _is_gui_available.reason = reason
    _is_gui_available.result = not reason

    return _is_gui_available.result