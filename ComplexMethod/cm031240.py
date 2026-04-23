async def _accept_connection2(
            self, protocol_factory, conn, extra,
            sslcontext=None, server=None,
            ssl_handshake_timeout=constants.SSL_HANDSHAKE_TIMEOUT,
            ssl_shutdown_timeout=constants.SSL_SHUTDOWN_TIMEOUT, context=None):
        protocol = None
        transport = None
        try:
            protocol = protocol_factory()
            waiter = self.create_future()
            if sslcontext:
                transport = self._make_ssl_transport(
                    conn, protocol, sslcontext, waiter=waiter,
                    server_side=True, extra=extra, server=server,
                    ssl_handshake_timeout=ssl_handshake_timeout,
                    ssl_shutdown_timeout=ssl_shutdown_timeout,
                    context=context)
            else:
                transport = self._make_socket_transport(
                    conn, protocol, waiter=waiter, extra=extra,
                    server=server, context=context)

            try:
                await waiter
            except BaseException:
                transport.close()
                # gh-109534: When an exception is raised by the SSLProtocol object the
                # exception set in this future can keep the protocol object alive and
                # cause a reference cycle.
                waiter = None
                raise
                # It's now up to the protocol to handle the connection.

        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            if self._debug:
                context = {
                    'message':
                        'Error on transport creation for incoming connection',
                    'exception': exc,
                }
                if protocol is not None:
                    context['protocol'] = protocol
                if transport is not None:
                    context['transport'] = transport
                self.call_exception_handler(context)