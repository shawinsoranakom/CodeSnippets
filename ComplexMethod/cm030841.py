def _do_ssl_handshake(self):
            try:
                self.socket.do_handshake()
            except ssl.SSLError as err:
                if err.args[0] in (ssl.SSL_ERROR_WANT_READ,
                                   ssl.SSL_ERROR_WANT_WRITE):
                    return
                elif err.args[0] == ssl.SSL_ERROR_EOF:
                    return self.handle_close()
                # TODO: SSLError does not expose alert information
                elif "SSLV3_ALERT_BAD_CERTIFICATE" in err.args[1]:
                    return self.handle_close()
                raise
            except OSError as err:
                if err.args[0] == errno.ECONNABORTED:
                    return self.handle_close()
            else:
                self._ssl_accepting = False