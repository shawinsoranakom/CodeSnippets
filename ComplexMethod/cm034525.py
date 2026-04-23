def _read_non_blocking_stdin(
        self,
        echo: bool = False,
        seconds: int | None = None,
        interrupt_input: c.Iterable[bytes] | None = None,
        complete_input: c.Iterable[bytes] | None = None,
    ) -> bytes:
        if self._final_q:
            raise NotImplementedError

        if seconds is not None:
            start = time.time()
        if interrupt_input is None:
            try:
                interrupt = termios.tcgetattr(sys.stdin.buffer.fileno())[6][termios.VINTR]
            except Exception:
                interrupt = b'\x03'  # value for Ctrl+C

        try:
            backspace_sequences = [termios.tcgetattr(self._stdin_fd)[6][termios.VERASE]]
        except Exception:
            # unsupported/not present, use default
            backspace_sequences = [b'\x7f', b'\x08']

        result_string = b''
        while seconds is None or (time.time() - start < seconds):
            key_pressed = None
            try:
                os.set_blocking(self._stdin_fd, False)
                while key_pressed is None and (seconds is None or (time.time() - start < seconds)):
                    key_pressed = self._stdin.read(1)
                    # throttle to prevent excess CPU consumption
                    time.sleep(C.DEFAULT_INTERNAL_POLL_INTERVAL)
            finally:
                os.set_blocking(self._stdin_fd, True)
                if key_pressed is None:
                    key_pressed = b''

            if (interrupt_input is None and key_pressed == interrupt) or (interrupt_input is not None and key_pressed.lower() in interrupt_input):
                clear_line(self._stdout)
                raise AnsiblePromptInterrupt('user interrupt')
            if (complete_input is None and key_pressed in (b'\r', b'\n')) or (complete_input is not None and key_pressed.lower() in complete_input):
                clear_line(self._stdout)
                break
            elif key_pressed in backspace_sequences:
                clear_line(self._stdout)
                result_string = result_string[:-1]
                if echo:
                    self._stdout.write(result_string)
                self._stdout.flush()
            else:
                result_string += key_pressed
        return result_string