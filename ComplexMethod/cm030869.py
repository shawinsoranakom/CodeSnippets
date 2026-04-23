def wrap_conn(self):
            try:
                self.sslconn = self.server.context.wrap_socket(
                    self.sock, server_side=True)
                self.server.selected_alpn_protocols.append(self.sslconn.selected_alpn_protocol())
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError) as e:
                # We treat ConnectionResetError as though it were an
                # SSLError - OpenSSL on Ubuntu abruptly closes the
                # connection when asked to use an unsupported protocol.
                #
                # BrokenPipeError is raised in TLS 1.3 mode, when OpenSSL
                # tries to send session tickets after handshake.
                # https://github.com/openssl/openssl/issues/6342
                #
                # ConnectionAbortedError is raised in TLS 1.3 mode, when OpenSSL
                # tries to send session tickets after handshake when using WinSock.
                self.server.conn_errors.append(str(e))
                if self.server.chatty:
                    handle_error("\n server:  bad connection attempt from " + repr(self.addr) + ":\n")
                self.running = False
                self.close()
                return False
            except (ssl.SSLError, OSError) as e:
                # OSError may occur with wrong protocols, e.g. both
                # sides use PROTOCOL_TLS_SERVER.
                #
                # XXX Various errors can have happened here, for example
                # a mismatching protocol version, an invalid certificate,
                # or a low-level bug. This should be made more discriminating.
                #
                # bpo-31323: Store the exception as string to prevent
                # a reference leak: server -> conn_errors -> exception
                # -> traceback -> self (ConnectionHandler) -> server
                self.server.conn_errors.append(str(e))
                if self.server.chatty:
                    handle_error("\n server:  bad connection attempt from " + repr(self.addr) + ":\n")

                # bpo-44229, bpo-43855, bpo-44237, and bpo-33450:
                # Ignore spurious EPROTOTYPE returned by write() on macOS.
                # See also http://erickt.github.io/blog/2014/11/19/adventures-in-debugging-a-potential-osx-kernel-bug/
                if e.errno != errno.EPROTOTYPE and sys.platform != "darwin":
                    self.running = False
                    self.close()
                return False
            else:
                self.server.shared_ciphers.append(self.sslconn.shared_ciphers())
                if self.server.context.verify_mode == ssl.CERT_REQUIRED:
                    cert = self.sslconn.getpeercert()
                    if support.verbose and self.server.chatty:
                        sys.stdout.write(" client cert is " + pprint.pformat(cert) + "\n")
                    cert_binary = self.sslconn.getpeercert(True)
                    if support.verbose and self.server.chatty:
                        if cert_binary is None:
                            sys.stdout.write(" client did not provide a cert\n")
                        else:
                            sys.stdout.write(f" cert binary is {len(cert_binary)}b\n")
                cipher = self.sslconn.cipher()
                if support.verbose and self.server.chatty:
                    sys.stdout.write(" server: connection cipher is now " + str(cipher) + "\n")
                return True