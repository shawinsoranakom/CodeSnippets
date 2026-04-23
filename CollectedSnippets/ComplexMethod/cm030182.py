def complete(self, text, state):
        import readline

        if state == 0:
            self.completion_matches = []
            if self.state not in ("pdb", "interact"):
                return None

            origline = readline.get_line_buffer()
            line = origline.lstrip()
            if self.multiline_block:
                # We're completing a line contained in a multi-line block.
                # Force the remote to treat it as a Python expression.
                line = "! " + line
            offset = len(origline) - len(line)
            begidx = readline.get_begidx() - offset
            endidx = readline.get_endidx() - offset

            msg = {
                "complete": {
                    "text": text,
                    "line": line,
                    "begidx": begidx,
                    "endidx": endidx,
                }
            }

            self._send(**msg)
            if self.write_failed:
                return None

            payload = self._readline()
            if not payload:
                return None

            payload = json.loads(payload)
            if "completions" not in payload:
                raise RuntimeError(
                    f"Failed to get valid completions. Got: {payload}"
                )

            self.completion_matches = payload["completions"]
        try:
            return self.completion_matches[state]
        except IndexError:
            return None