def main(listener_fd, alive_r, preload, main_path=None, sys_path=None,
         *, sys_argv=None, authkey_r=None, on_error='ignore'):
    """Run forkserver."""
    if authkey_r is not None:
        try:
            authkey = os.read(authkey_r, _AUTHKEY_LEN)
            assert len(authkey) == _AUTHKEY_LEN, f'{len(authkey)} < {_AUTHKEY_LEN}'
        finally:
            os.close(authkey_r)
    else:
        authkey = b''

    _handle_preload(preload, main_path, sys_path, sys_argv, on_error)

    util._close_stdin()

    sig_r, sig_w = os.pipe()
    os.set_blocking(sig_r, False)
    os.set_blocking(sig_w, False)

    def sigchld_handler(*_unused):
        # Dummy signal handler, doesn't do anything
        pass

    handlers = {
        # unblocking SIGCHLD allows the wakeup fd to notify our event loop
        signal.SIGCHLD: sigchld_handler,
        # protect the process from ^C
        signal.SIGINT: signal.SIG_IGN,
        }
    old_handlers = {sig: signal.signal(sig, val)
                    for (sig, val) in handlers.items()}

    # calling os.write() in the Python signal handler is racy
    signal.set_wakeup_fd(sig_w)

    # map child pids to client fds
    pid_to_fd = {}

    with socket.socket(socket.AF_UNIX, fileno=listener_fd) as listener, \
         selectors.DefaultSelector() as selector:
        _forkserver._forkserver_address = listener.getsockname()

        selector.register(listener, selectors.EVENT_READ)
        selector.register(alive_r, selectors.EVENT_READ)
        selector.register(sig_r, selectors.EVENT_READ)

        while True:
            try:
                while True:
                    rfds = [key.fileobj for (key, events) in selector.select()]
                    if rfds:
                        break

                if alive_r in rfds:
                    # EOF because no more client processes left
                    assert os.read(alive_r, 1) == b'', "Not at EOF?"
                    raise SystemExit

                if sig_r in rfds:
                    # Got SIGCHLD
                    os.read(sig_r, 65536)  # exhaust
                    while True:
                        # Scan for child processes
                        try:
                            pid, sts = os.waitpid(-1, os.WNOHANG)
                        except ChildProcessError:
                            break
                        if pid == 0:
                            break
                        child_w = pid_to_fd.pop(pid, None)
                        if child_w is not None:
                            returncode = os.waitstatus_to_exitcode(sts)

                            # Send exit code to client process
                            try:
                                write_signed(child_w, returncode)
                            except BrokenPipeError:
                                # client vanished
                                pass
                            os.close(child_w)
                        else:
                            # This shouldn't happen really
                            warnings.warn('forkserver: waitpid returned '
                                          'unexpected pid %d' % pid)

                if listener in rfds:
                    # Incoming fork request
                    with listener.accept()[0] as s:
                        try:
                            if authkey:
                                wrapped_s = connection.Connection(s.fileno())
                                # The other side of this exchange happens in
                                # in connect_to_new_process().
                                try:
                                    connection.deliver_challenge(
                                            wrapped_s, authkey)
                                    connection.answer_challenge(
                                            wrapped_s, authkey)
                                finally:
                                    wrapped_s._detach()
                                    del wrapped_s
                            # Receive fds from client
                            fds = reduction.recvfds(s, MAXFDS_TO_SEND + 1)
                        except (EOFError, BrokenPipeError, AuthenticationError):
                            s.close()
                            continue
                        if len(fds) > MAXFDS_TO_SEND:
                            raise RuntimeError(
                                "Too many ({0:n}) fds to send".format(
                                    len(fds)))
                        child_r, child_w, *fds = fds
                        s.close()
                        pid = os.fork()
                        if pid == 0:
                            # Child
                            code = 1
                            try:
                                listener.close()
                                selector.close()
                                unused_fds = [alive_r, child_w, sig_r, sig_w]
                                unused_fds.extend(pid_to_fd.values())
                                atexit._clear()
                                atexit.register(util._exit_function)
                                code = _serve_one(child_r, fds,
                                                  unused_fds,
                                                  old_handlers)
                            except Exception:
                                sys.excepthook(*sys.exc_info())
                                sys.stderr.flush()
                            finally:
                                atexit._run_exitfuncs()
                                os._exit(code)
                        else:
                            # Send pid to client process
                            try:
                                write_signed(child_w, pid)
                            except BrokenPipeError:
                                # client vanished
                                pass
                            pid_to_fd[pid] = child_w
                            os.close(child_r)
                            for fd in fds:
                                os.close(fd)

            except OSError as e:
                if e.errno != errno.ECONNABORTED:
                    raise