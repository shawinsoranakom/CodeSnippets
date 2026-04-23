def _socket_setup(self) -> None:
        """Initialize sockets
        https://pyzmq.readthedocs.io/en/v19.0.0/morethanbindings.html#thread-safety
        """
        if self._pub is None:
            self._pub = self._ctx.socket(zmq.PUB)
            self._pub.set_hwm(self._hwm)
            # Heuristic: bind if wildcard / * present, else connect.
            # bind stable, connect volatile convention
            if self._endpoint is not None and (
                "*" in self._endpoint
                or "::" in self._endpoint
                or self._endpoint.startswith("ipc://")
                or self._endpoint.startswith("inproc://")
            ):
                self._pub.bind(self._endpoint)
            elif self._endpoint is not None:
                self._pub.connect(self._endpoint)

        # Set up replay socket: use ROUTER
        # 1) handles multiple REQ clients (identities)
        # 2) lets us send back one request → many replies (streamed events)
        # 3) works in our non‑blocking poll loop alongside PUB
        if self._replay_endpoint is not None:
            self._replay = self._ctx.socket(zmq.ROUTER)
            self._replay.bind(self._replay_endpoint)