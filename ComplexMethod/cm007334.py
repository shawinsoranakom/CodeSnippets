def _socks5_auth(self):
        packet = compat_struct_pack('!B', SOCKS5_VERSION)

        auth_methods = [Socks5Auth.AUTH_NONE]
        if self._proxy.username and self._proxy.password:
            auth_methods.append(Socks5Auth.AUTH_USER_PASS)

        packet += compat_struct_pack('!B', len(auth_methods))
        packet += compat_struct_pack('!{0}B'.format(len(auth_methods)), *auth_methods)

        self.sendall(packet)

        version, method = self._recv_bytes(2)

        self._check_response_version(SOCKS5_VERSION, version)

        if method == Socks5Auth.AUTH_NO_ACCEPTABLE or (
                method == Socks5Auth.AUTH_USER_PASS and (not self._proxy.username or not self._proxy.password)):
            self.close()
            raise Socks5Error(Socks5Auth.AUTH_NO_ACCEPTABLE)

        if method == Socks5Auth.AUTH_USER_PASS:
            username = self._proxy.username.encode('utf-8')
            password = self._proxy.password.encode('utf-8')
            packet = compat_struct_pack('!B', SOCKS5_USER_AUTH_VERSION)
            packet += self._len_and_data(username) + self._len_and_data(password)
            self.sendall(packet)

            version, status = self._recv_bytes(2)

            self._check_response_version(SOCKS5_USER_AUTH_VERSION, version)

            if status != SOCKS5_USER_AUTH_SUCCESS:
                self.close()
                raise Socks5Error(Socks5Error.ERR_GENERAL_FAILURE)