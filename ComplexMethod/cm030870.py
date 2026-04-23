def run(self):
            self.running = True
            if not self.server.starttls_server:
                if not self.wrap_conn():
                    return
            while self.running:
                try:
                    msg = self.read()
                    stripped = msg.strip()
                    if not stripped:
                        # eof, so quit this handler
                        self.running = False
                        try:
                            self.sock = self.sslconn.unwrap()
                        except OSError:
                            # Many tests shut the TCP connection down
                            # without an SSL shutdown. This causes
                            # unwrap() to raise OSError with errno=0!
                            pass
                        else:
                            self.sslconn = None
                        self.close()
                    elif stripped == b'over':
                        if support.verbose and self.server.connectionchatty:
                            sys.stdout.write(" server: client closed connection\n")
                        self.close()
                        return
                    elif (self.server.starttls_server and
                          stripped == b'STARTTLS'):
                        if support.verbose and self.server.connectionchatty:
                            sys.stdout.write(" server: read STARTTLS from client, sending OK...\n")
                        self.write(b"OK\n")
                        if not self.wrap_conn():
                            return
                    elif (self.server.starttls_server and self.sslconn
                          and stripped == b'ENDTLS'):
                        if support.verbose and self.server.connectionchatty:
                            sys.stdout.write(" server: read ENDTLS from client, sending OK...\n")
                        self.write(b"OK\n")
                        self.sock = self.sslconn.unwrap()
                        self.sslconn = None
                        if support.verbose and self.server.connectionchatty:
                            sys.stdout.write(" server: connection is now unencrypted...\n")
                    elif stripped == b'CB tls-unique':
                        if support.verbose and self.server.connectionchatty:
                            sys.stdout.write(" server: read CB tls-unique from client, sending our CB data...\n")
                        data = self.sslconn.get_channel_binding("tls-unique")
                        self.write(repr(data).encode("us-ascii") + b"\n")
                    elif stripped == b'PHA':
                        if support.verbose and self.server.connectionchatty:
                            sys.stdout.write(" server: initiating post handshake auth\n")
                        try:
                            self.sslconn.verify_client_post_handshake()
                        except ssl.SSLError as e:
                            self.write(repr(e).encode("us-ascii") + b"\n")
                        else:
                            self.write(b"OK\n")
                    elif stripped == b'HASCERT':
                        if self.sslconn.getpeercert() is not None:
                            self.write(b'TRUE\n')
                        else:
                            self.write(b'FALSE\n')
                    elif stripped == b'GETCERT':
                        cert = self.sslconn.getpeercert()
                        self.write(repr(cert).encode("us-ascii") + b"\n")
                    elif stripped == b'VERIFIEDCHAIN':
                        certs = self.sslconn._sslobj.get_verified_chain()
                        self.write(len(certs).to_bytes(1, "big") + b"\n")
                    elif stripped == b'UNVERIFIEDCHAIN':
                        certs = self.sslconn._sslobj.get_unverified_chain()
                        self.write(len(certs).to_bytes(1, "big") + b"\n")
                    else:
                        if (support.verbose and
                            self.server.connectionchatty):
                            ctype = (self.sslconn and "encrypted") or "unencrypted"
                            sys.stdout.write(" server: read %r (%s), sending back %r (%s)...\n"
                                             % (msg, ctype, msg.lower(), ctype))
                        self.write(msg.lower())
                except OSError as e:
                    # handles SSLError and socket errors
                    if isinstance(e, ConnectionError):
                        # OpenSSL 1.1.1 sometimes raises
                        # ConnectionResetError when connection is not
                        # shut down gracefully.
                        if self.server.chatty and support.verbose:
                            print(f" Connection reset by peer: {self.addr}")

                        self.close()
                        self.running = False
                        return
                    if self.server.chatty and support.verbose:
                        handle_error("Test server failure:\n")
                    try:
                        self.write(b"ERROR\n")
                    except OSError:
                        pass
                    self.close()
                    self.running = False