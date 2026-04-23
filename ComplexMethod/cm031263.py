async def create_connection(
            self, protocol_factory, host=None, port=None,
            *, ssl=None, family=0,
            proto=0, flags=0, sock=None,
            local_addr=None, server_hostname=None,
            ssl_handshake_timeout=None,
            ssl_shutdown_timeout=None,
            happy_eyeballs_delay=None, interleave=None,
            all_errors=False):
        """Connect to a TCP server.

        Create a streaming transport connection to a given internet host and
        port: socket family AF_INET or socket.AF_INET6 depending on host (or
        family if specified), socket type SOCK_STREAM. protocol_factory must be
        a callable returning a protocol instance.

        This method is a coroutine which will try to establish the connection
        in the background.  When successful, the coroutine returns a
        (transport, protocol) pair.
        """
        if server_hostname is not None and not ssl:
            raise ValueError('server_hostname is only meaningful with ssl')

        if server_hostname is None and ssl:
            # Use host as default for server_hostname.  It is an error
            # if host is empty or not set, e.g. when an
            # already-connected socket was passed or when only a port
            # is given.  To avoid this error, you can pass
            # server_hostname='' -- this will bypass the hostname
            # check.  (This also means that if host is a numeric
            # IP/IPv6 address, we will attempt to verify that exact
            # address; this will probably fail, but it is possible to
            # create a certificate for a specific IP address, so we
            # don't judge it here.)
            if not host:
                raise ValueError('You must set server_hostname '
                                 'when using ssl without a host')
            server_hostname = host

        if ssl_handshake_timeout is not None and not ssl:
            raise ValueError(
                'ssl_handshake_timeout is only meaningful with ssl')

        if ssl_shutdown_timeout is not None and not ssl:
            raise ValueError(
                'ssl_shutdown_timeout is only meaningful with ssl')

        if sock is not None:
            _check_ssl_socket(sock)

        if happy_eyeballs_delay is not None and interleave is None:
            # If using happy eyeballs, default to interleave addresses by family
            interleave = 1

        if host is not None or port is not None:
            if sock is not None:
                raise ValueError(
                    'host/port and sock can not be specified at the same time')

            infos = await self._ensure_resolved(
                (host, port), family=family,
                type=socket.SOCK_STREAM, proto=proto, flags=flags, loop=self)
            if not infos:
                raise OSError('getaddrinfo() returned empty list')

            if local_addr is not None:
                laddr_infos = await self._ensure_resolved(
                    local_addr, family=family,
                    type=socket.SOCK_STREAM, proto=proto,
                    flags=flags, loop=self)
                if not laddr_infos:
                    raise OSError('getaddrinfo() returned empty list')
            else:
                laddr_infos = None

            if interleave:
                infos = _interleave_addrinfos(infos, interleave)

            exceptions = []
            if happy_eyeballs_delay is None:
                # not using happy eyeballs
                for addrinfo in infos:
                    try:
                        sock = await self._connect_sock(
                            exceptions, addrinfo, laddr_infos)
                        break
                    except OSError:
                        continue
            else:  # using happy eyeballs
                sock = (await staggered.staggered_race(
                    (
                        # can't use functools.partial as it keeps a reference
                        # to exceptions
                        lambda addrinfo=addrinfo: self._connect_sock(
                            exceptions, addrinfo, laddr_infos
                        )
                        for addrinfo in infos
                    ),
                    happy_eyeballs_delay,
                    loop=self,
                ))[0]  # can't use sock, _, _ as it keeks a reference to exceptions

            if sock is None:
                exceptions = [exc for sub in exceptions for exc in sub]
                try:
                    if all_errors:
                        raise ExceptionGroup("create_connection failed", exceptions)
                    if len(exceptions) == 1:
                        raise exceptions[0]
                    elif exceptions:
                        # If they all have the same str(), raise one.
                        model = str(exceptions[0])
                        if all(str(exc) == model for exc in exceptions):
                            raise exceptions[0]
                        # Raise a combined exception so the user can see all
                        # the various error messages.
                        raise OSError('Multiple exceptions: {}'.format(
                            ', '.join(str(exc) for exc in exceptions)))
                    else:
                        # No exceptions were collected, raise a timeout error
                        raise TimeoutError('create_connection failed')
                finally:
                    exceptions = None

        else:
            if sock is None:
                raise ValueError(
                    'host and port was not specified and no sock specified')
            if sock.type != socket.SOCK_STREAM:
                # We allow AF_INET, AF_INET6, AF_UNIX as long as they
                # are SOCK_STREAM.
                # We support passing AF_UNIX sockets even though we have
                # a dedicated API for that: create_unix_connection.
                # Disallowing AF_UNIX in this method, breaks backwards
                # compatibility.
                raise ValueError(
                    f'A Stream Socket was expected, got {sock!r}')

        transport, protocol = await self._create_connection_transport(
            sock, protocol_factory, ssl, server_hostname,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout)
        if self._debug:
            # Get the socket from the transport because SSL transport closes
            # the old socket and creates a new SSL socket
            sock = transport.get_extra_info('socket')
            logger.debug("%r connected to %s:%r: (%r, %r)",
                         sock, host, port, transport, protocol)
        return transport, protocol