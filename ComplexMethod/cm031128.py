def _run(self):
        while self._active:
            if self._clients >= self._max_clients:
                return

            r, w, x = select.select(
                [self._sock, self._s1], [], [], self._timeout)

            if self._s1 in r:
                return

            if self._sock in r:
                try:
                    conn, addr = self._sock.accept()
                except BlockingIOError:
                    continue
                except socket.timeout:
                    if not self._active:
                        return
                    else:
                        raise
                else:
                    self._clients += 1
                    conn.settimeout(self._timeout)
                    try:
                        with conn:
                            self._handle_client(conn)
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except BaseException as ex:
                        self._active = False
                        try:
                            raise
                        finally:
                            self._test._abort_socket_test(ex)