def _reader(self):
        try:
            sentinel = "" if self.text else b""
            for raw_line in iter(self.pipe.readline, sentinel):
                if not self.text:
                    line = raw_line.decode(self.encoding, self.errors)
                else:
                    line = raw_line
                line = line.rstrip("\r\n")
                if self.echo:
                    if "platform is" not in line:
                        print(f"{self.name}: {line}")

                with self.lock:
                    self.buf.append(line)

                if self.ready_regex is not None and self.ready_regex.search(line):
                    self.ready_event.set()

        finally:
            try:
                self.pipe.close()
            except Exception:
                pass
            self.closed_event.set()