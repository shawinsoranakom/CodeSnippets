def ensure_running(self):
        '''Make sure that a fork server is running.

        This can be called from any process.  Note that usually a child
        process will just reuse the forkserver started by its parent, so
        ensure_running() will do nothing.
        '''
        with self._lock:
            resource_tracker.ensure_running()
            if self._forkserver_pid is not None:
                # forkserver was launched before, is it still running?
                pid, status = os.waitpid(self._forkserver_pid, os.WNOHANG)
                if not pid:
                    # still alive
                    return
                # dead, launch it again
                os.close(self._forkserver_alive_fd)
                self._forkserver_authkey = None
                self._forkserver_address = None
                self._forkserver_alive_fd = None
                self._forkserver_pid = None

            # gh-144503: sys_argv is passed as real argv elements after the
            # ``-c cmd`` rather than repr'd into main_kws so that a large
            # parent sys.argv cannot push the single ``-c`` command string
            # over the OS per-argument length limit (MAX_ARG_STRLEN on Linux).
            # The child sees them as sys.argv[1:].
            cmd = ('import sys; '
                   'from multiprocessing.forkserver import main; '
                   'main(%d, %d, %r, sys_argv=sys.argv[1:], **%r)')

            main_kws = {}
            sys_argv = None
            if self._preload_modules:
                data = spawn.get_preparation_data('ignore')
                if 'sys_path' in data:
                    main_kws['sys_path'] = data['sys_path']
                if 'init_main_from_path' in data:
                    main_kws['main_path'] = data['init_main_from_path']
                if 'sys_argv' in data:
                    sys_argv = data['sys_argv']
                if self._preload_on_error != 'ignore':
                    main_kws['on_error'] = self._preload_on_error

            with socket.socket(socket.AF_UNIX) as listener:
                address = connection.arbitrary_address('AF_UNIX')
                listener.bind(address)
                if not util.is_abstract_socket_namespace(address):
                    os.chmod(address, 0o600)
                listener.listen()

                # all client processes own the write end of the "alive" pipe;
                # when they all terminate the read end becomes ready.
                alive_r, alive_w = os.pipe()
                # A short lived pipe to initialize the forkserver authkey.
                authkey_r, authkey_w = os.pipe()
                try:
                    fds_to_pass = [listener.fileno(), alive_r, authkey_r]
                    main_kws['authkey_r'] = authkey_r
                    cmd %= (listener.fileno(), alive_r, self._preload_modules,
                            main_kws)
                    exe = spawn.get_executable()
                    args = [exe] + util._args_from_interpreter_flags()
                    args += ['-c', cmd]
                    if sys_argv is not None:
                        args += sys_argv
                    pid = util.spawnv_passfds(exe, args, fds_to_pass)
                except:
                    os.close(alive_w)
                    os.close(authkey_w)
                    raise
                finally:
                    os.close(alive_r)
                    os.close(authkey_r)
                # Authenticate our control socket to prevent access from
                # processes we have not shared this key with.
                try:
                    self._forkserver_authkey = os.urandom(_AUTHKEY_LEN)
                    os.write(authkey_w, self._forkserver_authkey)
                finally:
                    os.close(authkey_w)
                self._forkserver_address = address
                self._forkserver_alive_fd = alive_w
                self._forkserver_pid = pid