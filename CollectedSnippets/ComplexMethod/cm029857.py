def ntransfercmd(self, cmd, rest=None):
        """Initiate a transfer over the data connection.

        If the transfer is active, send a port command and the
        transfer command, and accept the connection.  If the server is
        passive, send a pasv command, connect to it, and start the
        transfer command.  Either way, return the socket for the
        connection and the expected size of the transfer.  The
        expected size may be None if it could not be determined.

        Optional 'rest' argument can be a string that is sent as the
        argument to a REST command.  This is essentially a server
        marker used to tell the server to skip over any data up to the
        given marker.
        """
        size = None
        if self.passiveserver:
            host, port = self.makepasv()
            conn = socket.create_connection((host, port), self.timeout,
                                            source_address=self.source_address)
            try:
                if rest is not None:
                    self.sendcmd("REST %s" % rest)
                resp = self.sendcmd(cmd)
                # Some servers apparently send a 200 reply to
                # a LIST or STOR command, before the 150 reply
                # (and way before the 226 reply). This seems to
                # be in violation of the protocol (which only allows
                # 1xx or error messages for LIST), so we just discard
                # this response.
                if resp[0] == '2':
                    resp = self.getresp()
                if resp[0] != '1':
                    raise error_reply(resp)
            except:
                conn.close()
                raise
        else:
            with self.makeport() as sock:
                if rest is not None:
                    self.sendcmd("REST %s" % rest)
                resp = self.sendcmd(cmd)
                # See above.
                if resp[0] == '2':
                    resp = self.getresp()
                if resp[0] != '1':
                    raise error_reply(resp)
                conn, sockaddr = sock.accept()
                if self.timeout is not _GLOBAL_DEFAULT_TIMEOUT:
                    conn.settimeout(self.timeout)
        if resp[:3] == '150':
            # this is conditional in case we received a 125
            size = parse150(resp)
        return conn, size