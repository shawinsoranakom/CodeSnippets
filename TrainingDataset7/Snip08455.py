def lock(f, flags):
        hfile = msvcrt.get_osfhandle(_fd(f))
        overlapped = OVERLAPPED()
        ret = LockFileEx(hfile, flags, 0, 0, 0xFFFF0000, byref(overlapped))
        return bool(ret)