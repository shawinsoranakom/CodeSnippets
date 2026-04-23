def _accept_connection(
            self, protocol_factory, sock,
            sslcontext=None, server=None, backlog=100,
            ssl_handshake_timeout=constants.SSL_HANDSHAKE_TIMEOUT,
            ssl_shutdown_timeout=constants.SSL_SHUTDOWN_TIMEOUT, context=None):
        # This method is only called once for each event loop tick where the
        # listening socket has triggered an EVENT_READ. There may be multiple
        # connections waiting for an .accept() so it is called in a loop.
        # See https://bugs.python.org/issue27906 for more details.
        for _ in range(backlog + 1):
            try:
                conn, addr = sock.accept()
                if self._debug:
                    logger.debug("%r got a new connection from %r: %r",
                                 server, addr, conn)
                conn.setblocking(False)
            except ConnectionAbortedError:
                # Discard connections that were aborted before accept().
                continue
            except (BlockingIOError, InterruptedError):
                # Early exit because of a signal or
                # the socket accept buffer is empty.
                return
            except OSError as exc:
                # There's nowhere to send the error, so just log it.
                if exc.errno in (errno.EMFILE, errno.ENFILE,
                                 errno.ENOBUFS, errno.ENOMEM):
                    # Some platforms (e.g. Linux keep reporting the FD as
                    # ready, so we remove the read handler temporarily.
                    # We'll try again in a while.
                    self.call_exception_handler({
                        'message': 'socket.accept() out of system resource',
                        'exception': exc,
                        'socket': trsock.TransportSocket(sock),
                    })
                    self._remove_reader(sock.fileno())
                    self.call_later(constants.ACCEPT_RETRY_DELAY,
                                    self._start_serving,
                                    protocol_factory, sock, sslcontext, server,
                                    backlog, ssl_handshake_timeout,
                                    ssl_shutdown_timeout, context)
                else:
                    raise  # The event loop will catch, log and ignore it.
            else:
                extra = {'peername': addr}
                conn_context = context.copy() if context is not None else None
                accept = self._accept_connection2(
                    protocol_factory, conn, extra, sslcontext, server,
                    ssl_handshake_timeout, ssl_shutdown_timeout, context=conn_context)
                self.create_task(accept, context=conn_context)