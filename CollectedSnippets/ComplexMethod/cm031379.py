def _check_close(self):
        conn = self.headers.get("connection")
        if self.version == 11:
            # An HTTP/1.1 proxy is assumed to stay open unless
            # explicitly closed.
            if conn and "close" in conn.lower():
                return True
            return False

        # Some HTTP/1.0 implementations have support for persistent
        # connections, using rules different than HTTP/1.1.

        # For older HTTP, Keep-Alive indicates persistent connection.
        if self.headers.get("keep-alive"):
            return False

        # At least Akamai returns a "Connection: Keep-Alive" header,
        # which was supposed to be sent by the client.
        if conn and "keep-alive" in conn.lower():
            return False

        # Proxy-Connection is a netscape hack.
        pconn = self.headers.get("proxy-connection")
        if pconn and "keep-alive" in pconn.lower():
            return False

        # otherwise, assume it will close
        return True