def handle(self):
        sleep = self.socks_kwargs.get('sleep')
        if sleep:
            time.sleep(sleep)
        version, nmethods = self.connection.recv(2)
        assert version == SOCKS5_VERSION
        methods = list(self.connection.recv(nmethods))

        auth = self.socks_kwargs.get('auth')

        if auth is not None and Socks5Auth.AUTH_USER_PASS not in methods:
            self.connection.sendall(struct.pack('!BB', SOCKS5_VERSION, Socks5Auth.AUTH_NO_ACCEPTABLE))
            self.server.close_request(self.request)
            return

        elif Socks5Auth.AUTH_USER_PASS in methods:
            self.connection.sendall(struct.pack('!BB', SOCKS5_VERSION, Socks5Auth.AUTH_USER_PASS))

            _, user_len = struct.unpack('!BB', self.connection.recv(2))
            username = self.connection.recv(user_len).decode()
            pass_len = ord(self.connection.recv(1))
            password = self.connection.recv(pass_len).decode()

            if username == auth[0] and password == auth[1]:
                self.connection.sendall(struct.pack('!BB', SOCKS5_USER_AUTH_VERSION, SOCKS5_USER_AUTH_SUCCESS))
            else:
                self.connection.sendall(struct.pack('!BB', SOCKS5_USER_AUTH_VERSION, SOCKS5_USER_AUTH_FAILURE))
                self.server.close_request(self.request)
                return

        elif Socks5Auth.AUTH_NONE in methods:
            self.connection.sendall(struct.pack('!BB', SOCKS5_VERSION, Socks5Auth.AUTH_NONE))
        else:
            self.connection.sendall(struct.pack('!BB', SOCKS5_VERSION, Socks5Auth.AUTH_NO_ACCEPTABLE))
            self.server.close_request(self.request)
            return

        version, command, _, address_type = struct.unpack('!BBBB', self.connection.recv(4))
        socks_info = {
            'version': version,
            'auth_methods': methods,
            'command': command,
            'client_address': self.client_address,
            'ipv4_address': None,
            'domain_address': None,
            'ipv6_address': None,
        }
        if address_type == Socks5AddressType.ATYP_IPV4:
            socks_info['ipv4_address'] = socket.inet_ntoa(self.connection.recv(4))
        elif address_type == Socks5AddressType.ATYP_DOMAINNAME:
            socks_info['domain_address'] = self.connection.recv(ord(self.connection.recv(1))).decode()
        elif address_type == Socks5AddressType.ATYP_IPV6:
            socks_info['ipv6_address'] = socket.inet_ntop(socket.AF_INET6, self.connection.recv(16))
        else:
            self.server.close_request(self.request)

        socks_info['port'] = struct.unpack('!H', self.connection.recv(2))[0]

        # dummy response, the returned IP is just a placeholder
        self.connection.sendall(struct.pack(
            '!BBBBIH', SOCKS5_VERSION, self.socks_kwargs.get('reply', Socks5Reply.SUCCEEDED), 0x0, 0x1, 0x7f000001, 40000))

        self.request_handler_class(self.request, self.client_address, self.server, socks_info=socks_info)