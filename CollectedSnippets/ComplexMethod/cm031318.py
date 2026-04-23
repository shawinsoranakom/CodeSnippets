async def create_unix_connection(
            self, protocol_factory, path=None, *,
            ssl=None, sock=None,
            server_hostname=None,
            ssl_handshake_timeout=None,
            ssl_shutdown_timeout=None):
        assert server_hostname is None or isinstance(server_hostname, str)
        if ssl:
            if server_hostname is None:
                raise ValueError(
                    'you have to pass server_hostname when using ssl')
        else:
            if server_hostname is not None:
                raise ValueError('server_hostname is only meaningful with ssl')
            if ssl_handshake_timeout is not None:
                raise ValueError(
                    'ssl_handshake_timeout is only meaningful with ssl')
            if ssl_shutdown_timeout is not None:
                raise ValueError(
                    'ssl_shutdown_timeout is only meaningful with ssl')

        if path is not None:
            if sock is not None:
                raise ValueError(
                    'path and sock can not be specified at the same time')

            path = os.fspath(path)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
            try:
                sock.setblocking(False)
                await self.sock_connect(sock, path)
            except:
                sock.close()
                raise

        else:
            if sock is None:
                raise ValueError('no path and sock were specified')
            if (sock.family != socket.AF_UNIX or
                    sock.type != socket.SOCK_STREAM):
                raise ValueError(
                    f'A UNIX Domain Stream Socket was expected, got {sock!r}')
            sock.setblocking(False)

        transport, protocol = await self._create_connection_transport(
            sock, protocol_factory, ssl, server_hostname,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout)
        return transport, protocol