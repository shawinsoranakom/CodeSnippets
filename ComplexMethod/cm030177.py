def _read_reply(self):
        # Loop until we get a 'reply' or 'signal' from the client,
        # processing out-of-band 'complete' requests as they arrive.
        while True:
            if self._write_failed:
                raise EOFError

            msg = self._sockfile.readline()
            if not msg:
                raise EOFError

            try:
                payload = json.loads(msg)
            except json.JSONDecodeError:
                self.error(f"Disconnecting: client sent invalid JSON {msg!r}")
                raise EOFError

            match payload:
                case {"reply": str(reply)}:
                    return reply
                case {"signal": str(signal)}:
                    if signal == "INT":
                        raise KeyboardInterrupt
                    elif signal == "EOF":
                        raise EOFError
                    else:
                        self.error(
                            f"Received unrecognized signal: {signal}"
                        )
                        # Our best hope of recovering is to pretend we
                        # got an EOF to exit whatever mode we're in.
                        raise EOFError
                case {
                    "complete": {
                        "text": str(text),
                        "line": str(line),
                        "begidx": int(begidx),
                        "endidx": int(endidx),
                    }
                }:
                    items = self._complete_any(text, line, begidx, endidx)
                    self._send(completions=items)
                    continue
            # Valid JSON, but doesn't meet the schema.
            self.error(f"Ignoring invalid message from client: {msg}")