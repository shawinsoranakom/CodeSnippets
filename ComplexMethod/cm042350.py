def send_apdu(self, apdu: bytes) -> tuple[bytes, int, int]:
    for attempt in range(SEND_APDU_RETRIES):
      try:
        if not self.channel:
          self.open_isdr()
        hex_payload = apdu.hex().upper()
        for line in self.query(f'AT+CGLA={self.channel},{len(hex_payload)},"{hex_payload}"'):
          if line.startswith("+CGLA:"):
            parts = line.split(":", 1)[1].split(",", 1)
            if len(parts) == 2:
              data = bytes.fromhex(parts[1].strip().strip('"'))
              if len(data) >= 2:
                return data[:-2], data[-2], data[-1]
        raise RuntimeError("Missing +CGLA response")
      except (RuntimeError, ValueError):
        self.channel = None
        if attempt == SEND_APDU_RETRIES - 1:
          raise
    raise RuntimeError("send_apdu failed")