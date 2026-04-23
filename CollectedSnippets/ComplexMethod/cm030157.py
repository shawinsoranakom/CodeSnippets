def _read_code(self, line):
        buffer = line
        is_await_code = False
        code = None
        try:
            if (code := codeop.compile_command(line + '\n', '<stdin>', 'single')) is None:
                # Multi-line mode
                with self._enable_multiline_input():
                    buffer = line
                    continue_prompt = "...   "
                    while (code := codeop.compile_command(buffer, '<stdin>', 'single')) is None:
                        if self.use_rawinput:
                            try:
                                line = input(continue_prompt)
                            except (EOFError, KeyboardInterrupt):
                                self.lastcmd = ""
                                print('\n')
                                return None, None, False
                        else:
                            self.stdout.write(continue_prompt)
                            self.stdout.flush()
                            line = self.stdin.readline()
                            if not len(line):
                                self.lastcmd = ""
                                self.stdout.write('\n')
                                self.stdout.flush()
                                return None, None, False
                            else:
                                line = line.rstrip('\r\n')
                        if line.isspace():
                            # empty line, just continue
                            buffer += '\n'
                        else:
                            buffer += '\n' + line
                    self.lastcmd = buffer
        except SyntaxError as e:
            # Maybe it's an await expression/statement
            if (
                self.async_shim_frame is not None
                and e.msg == "'await' outside function"
            ):
                is_await_code = True
            else:
                raise

        return code, buffer, is_await_code