def add_data(self, log_time: float, incoming: bytes) -> list[bytes]:
    self.last_log_time = log_time
    out: list[bytes] = []
    if not incoming:
      return out
    self.buf += incoming

    while True:
      # find preamble
      if len(self.buf) < 2:
        break
      start = self.buf.find(b"\xb5\x62")
      if start < 0:
        # no preamble in buffer
        self.buf.clear()
        break
      if start > 0:
        # drop garbage before preamble
        self.buf = self.buf[start:]

      if len(self.buf) < self.HEADER_SIZE:
        break

      length_le = int.from_bytes(self.buf[4:6], 'little', signed=False)
      total_len = self.HEADER_SIZE + length_le + self.CHECKSUM_SIZE
      if len(self.buf) < total_len:
        break

      candidate = bytes(self.buf[:total_len])
      if self._checksum_ok(candidate):
        out.append(candidate)
        # consume this frame
        self.buf = self.buf[total_len:]
      else:
        # drop first byte and retry
        self.buf = self.buf[1:]

    return out