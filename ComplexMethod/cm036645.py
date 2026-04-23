def receive_replay(self, socket_idx: int = 0) -> list[tuple[int, SampleBatch]]:
        """Receive replayed messages from a specific replay socket"""
        if not self.replay_sockets:
            raise ValueError("Replay sockets not initialized")
        if socket_idx >= len(self.replay_sockets):
            raise ValueError(f"Invalid socket index {socket_idx}")

        replay_socket = self.replay_sockets[socket_idx]
        replayed: list[tuple[int, SampleBatch]] = []
        while True:
            try:
                if not replay_socket.poll(1000):
                    break

                frames = replay_socket.recv_multipart()
                if not frames or not frames[-1]:
                    # End of replay marker
                    break

                seq_bytes, payload = frames
                seq = int.from_bytes(seq_bytes, "big")
                data = self.decoder.decode(payload)
                replayed.append((seq, data))
            except zmq.ZMQError as _:
                break

        return replayed