def _spawnvef(mode, file, args, env, func):
        # Internal helper; func is the exec*() function to use
        if not isinstance(args, (tuple, list)):
            raise TypeError('argv must be a tuple or a list')
        if not args or not args[0]:
            raise ValueError('argv first element cannot be empty')
        pid = fork()
        if not pid:
            # Child
            try:
                if env is None:
                    func(file, args)
                else:
                    func(file, args, env)
            except:
                _exit(127)
        else:
            # Parent
            if mode == P_NOWAIT:
                return pid # Caller is responsible for waiting!
            while 1:
                wpid, sts = waitpid(pid, 0)
                if WIFSTOPPED(sts):
                    continue

                return waitstatus_to_exitcode(sts)