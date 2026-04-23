def _winrm_write_stdin(self, command_id: str, stdin_iterator: t.Iterable[tuple[bytes, bool]]) -> None:
        for (data, is_last) in stdin_iterator:
            for attempt in range(1, 4):
                try:
                    self._winrm_send_input(self.protocol, self.shell_id, command_id, data, eof=is_last)

                except WinRMOperationTimeoutError:
                    # A WSMan OperationTimeout can be received for a Send
                    # operation when the server is under severe load. On manual
                    # testing the input is still processed and it's safe to
                    # continue. As the calling method still tries to wait for
                    # the proc to end if this failed it shouldn't hurt to just
                    # treat this as a warning.
                    display.warning(
                        "WSMan OperationTimeout during send input, attempting to continue. "
                        "If this continues to occur, try increasing the connection_timeout "
                        "value for this host."
                    )
                    if not is_last:
                        time.sleep(5)

                except WinRMError as e:
                    # Error 170 == ERROR_BUSY. This could be the result of a
                    # timed out Send from above still being processed on the
                    # server. Add a 5 second delay and try up to 3 times before
                    # fully giving up.
                    # pywinrm does not expose the internal WSMan fault details
                    # through an actual object but embeds it as a repr.
                    if attempt == 3 or "'wsmanfault_code': '170'" not in str(e):
                        raise

                    display.warning(f"WSMan send failed on attempt {attempt} as the command is busy, trying to send data again")
                    time.sleep(5)
                    continue

                break