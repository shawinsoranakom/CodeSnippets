def _setup_socks5(self, address):
        destaddr, port = address

        family, ipaddr = self._resolve_address(destaddr, None, use_remote_dns=True)

        self._socks5_auth()

        reserved = 0
        packet = struct.pack('!BBB', SOCKS5_VERSION, Socks5Command.CMD_CONNECT, reserved)
        if ipaddr is None:
            destaddr = destaddr.encode()
            packet += struct.pack('!B', Socks5AddressType.ATYP_DOMAINNAME)
            packet += self._len_and_data(destaddr)
        elif family == socket.AF_INET:
            packet += struct.pack('!B', Socks5AddressType.ATYP_IPV4) + ipaddr
        elif family == socket.AF_INET6:
            packet += struct.pack('!B', Socks5AddressType.ATYP_IPV6) + ipaddr
        packet += struct.pack('!H', port)

        self.sendall(packet)

        version, status, reserved, atype = self._recv_bytes(4)

        self._check_response_version(SOCKS5_VERSION, version)

        if status != Socks5Error.ERR_SUCCESS:
            self.close()
            raise Socks5Error(status)

        if atype == Socks5AddressType.ATYP_IPV4:
            destaddr = self.recvall(4)
        elif atype == Socks5AddressType.ATYP_DOMAINNAME:
            alen = compat_ord(self.recv(1))
            destaddr = self.recvall(alen)
        elif atype == Socks5AddressType.ATYP_IPV6:
            destaddr = self.recvall(16)
        destport = struct.unpack('!H', self.recvall(2))[0]

        return (destaddr, destport)