def _handle_request(self, s_src: socket.socket):
        try:
            s_dst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            with s_src as s_src, s_dst as s_dst:
                s_dst.connect((self._target_address, self._target_port))

                sockets = [s_src, s_dst]
                while not self._stopped.is_set():
                    s_read, _, _ = select.select(sockets, [], [], 1)

                    for s in s_read:
                        data = s.recv(self._buffer_size)
                        if not data:
                            return

                        if s == s_src:
                            forward, response = data, None
                            if self._handler:
                                forward, response = self._handler(data)
                            if forward is not None:
                                s_dst.sendall(forward)
                            elif response is not None:
                                s_src.sendall(response)
                                return
                        elif s == s_dst:
                            s_src.sendall(data)
        except Exception as e:
            LOG.error(
                "Error while handling request from %s to %s:%s: %s",
                s_src.getpeername(),
                self._target_address,
                self._target_port,
                e,
            )