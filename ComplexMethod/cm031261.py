def _check_sendfile_params(self, sock, file, offset, count):
        if 'b' not in getattr(file, 'mode', 'b'):
            raise ValueError("file should be opened in binary mode")
        if not sock.type == socket.SOCK_STREAM:
            raise ValueError("only SOCK_STREAM type sockets are supported")
        if count is not None:
            if not isinstance(count, int):
                raise TypeError(
                    "count must be a positive integer (got {!r})".format(count))
            if count <= 0:
                raise ValueError(
                    "count must be a positive integer (got {!r})".format(count))
        if not isinstance(offset, int):
            raise TypeError(
                "offset must be a non-negative integer (got {!r})".format(
                    offset))
        if offset < 0:
            raise ValueError(
                "offset must be a non-negative integer (got {!r})".format(
                    offset))