def get_lockdata():
        try:
            os.O_LARGEFILE
        except AttributeError:
            start_len = "ll"
        else:
            start_len = "qq"

        if (
            sys.platform.startswith(('netbsd', 'freebsd', 'openbsd'))
            or is_apple
        ):
            if struct.calcsize('l') == 8:
                off_t = 'l'
                pid_t = 'i'
            else:
                off_t = 'lxxxx'
                pid_t = 'l'
            lockdata = struct.pack(off_t + off_t + pid_t + 'hh', 0, 0, 0,
                                   fcntl.F_WRLCK, 0)
        elif sys.platform.startswith('gnukfreebsd'):
            lockdata = struct.pack('qqihhi', 0, 0, 0, fcntl.F_WRLCK, 0, 0)
        elif sys.platform in ['hp-uxB', 'unixware7']:
            lockdata = struct.pack('hhlllii', fcntl.F_WRLCK, 0, 0, 0, 0, 0, 0)
        else:
            lockdata = struct.pack('hh'+start_len+'hh', fcntl.F_WRLCK, 0, 0, 0, 0, 0)
        if lockdata:
            if verbose:
                print('struct.pack: ', repr(lockdata))
        return lockdata