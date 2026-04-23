def handle_stream_output(self, stream, is_error_stream):
        try:
            for line in iter(stream.readline, ""):
                if self.verbose:
                    print(f"Received output line:\n{line}\n---")

                line = self.line_postprocessor(line)

                if line is None:
                    continue  # `line = None` is the postprocessor's signal to discard completely

                if self.detect_active_line(line):
                    active_line = self.detect_active_line(line)
                    self.output_queue.put(
                        {
                            "type": "console",
                            "format": "active_line",
                            "content": active_line,
                        }
                    )
                    # Sometimes there's a little extra on the same line, so be sure to send that out
                    line = re.sub(r"##active_line\d+##", "", line)
                    if line:
                        self.output_queue.put(
                            {"type": "console", "format": "output", "content": line}
                        )
                elif self.detect_end_of_execution(line):
                    # Sometimes there's a little extra on the same line, so be sure to send that out
                    line = line.replace("##end_of_execution##", "").strip()
                    if line:
                        self.output_queue.put(
                            {"type": "console", "format": "output", "content": line}
                        )
                    self.done.set()
                elif is_error_stream and "KeyboardInterrupt" in line:
                    self.output_queue.put(
                        {
                            "type": "console",
                            "format": "output",
                            "content": "KeyboardInterrupt",
                        }
                    )
                    time.sleep(0.1)
                    self.done.set()
                else:
                    self.output_queue.put(
                        {"type": "console", "format": "output", "content": line}
                    )
        except ValueError as e:
            if "operation on closed file" in str(e):
                if self.verbose:
                    print("Stream closed while reading.")
            else:
                raise e