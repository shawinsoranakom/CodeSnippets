def _socks5_auth(self):
        packet = struct.pack('!B', SOCKS5_VERSION)

        auth_methods = [Socks5Auth.AUTH_NONE]
        if self._proxy.username and self._proxy.password:
            auth_methods.append(Socks5Auth.AUTH_USER_PASS)

        packet += struct.pack('!B', len(auth_methods))
        packet += struct.pack(f'!{len(auth_methods)}B', *auth_methods)

        self.sendall(packet)

        version, method = self._recv_bytes(2)

        self._check_response_version(SOCKS5_VERSION, version)

        if method == Socks5Auth.AUTH_NO_ACCEPTABLE or (
                method == Socks5Auth.AUTH_USER_PASS and (not self._proxy.username or not self._proxy.password)):
            self.close()
            raise Socks5Error(Socks5Auth.AUTH_NO_ACCEPTABLE)

        if method == Socks5Auth.AUTH_USER_PASS:
            username = self._proxy.username.encode()
            password = self._proxy.password.encode()
            packet = struct.pack('!B', SOCKS5_USER_AUTH_VERSION)
            packet += self._len_and_data(username) + self._len_and_data(password)
            self.sendall(packet)

            version, status = self._recv_bytes(2)

            self._check_response_version(SOCKS5_USER_AUTH_VERSION, version)

            if status != SOCKS5_USER_AUTH_SUCCESS:
                self.close()
                raise Socks5Error(Socks5Error.ERR_GENERAL_FAILURE)