def unlock(f):
        hfile = msvcrt.get_osfhandle(_fd(f))
        overlapped = OVERLAPPED()
        ret = UnlockFileEx(hfile, 0, 0, 0xFFFF0000, byref(overlapped))
        return bool(ret)