def get_messages(self):
        while self.state is not ConnectionState.CLOSED:
            try:
                readables = {
                    selector_key[0].fileobj
                    for selector_key in self.__selector.select(TimeoutManager.TIMEOUT)
                }
                if (
                    self._timeout_manager.has_keep_alive_timed_out()
                    and self.state is ConnectionState.OPEN
                ):
                    self._disconnect(CloseCode.KEEP_ALIVE_TIMEOUT)
                    continue
                if self._timeout_manager.has_frame_response_timed_out():
                    self._terminate()
                    continue
                if not readables and self._timeout_manager.should_send_ping_frame():
                    self._send_ping_frame()
                    continue
                if self.__cmd_queue in readables:
                    cmd, _, data = self.__cmd_queue.get_nowait()
                    self._process_control_command(cmd, data)
                    if self.state is ConnectionState.CLOSED:
                        continue
                if self.__socket in readables:
                    message = self._process_next_message()
                    if message is not None:
                        yield message
            except Exception as exc:
                self._handle_transport_error(exc)