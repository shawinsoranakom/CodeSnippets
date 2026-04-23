def _open_isdr_once(self) -> None:
    if self.channel:
      try:
        self.query(f"AT+CCHC={self.channel}")
      except RuntimeError:
        pass
      self.channel = None
    # drain any unsolicited responses before opening
    if self._serial and not self._use_dbus:
      try:
        self._serial.reset_input_buffer()
      except (OSError, serial.SerialException, termios.error):
        self._ensure_serial(reconnect=True)
    for line in self.query(f'AT+CCHO="{ISDR_AID}"'):
      if line.startswith("+CCHO:") and (ch := line.split(":", 1)[1].strip()):
        self.channel = ch
        return
    raise RuntimeError("Failed to open ISD-R application")