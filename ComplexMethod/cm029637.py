def readline(self, input):
        """Read a line of password input with echo character support."""
        while True:
            assert self.cursor_pos >= 0
            char = input.read(1)
            if self.is_eol(char):
                break
            # Handle literal next mode first as Ctrl+V quotes characters.
            elif self.literal_next:
                self.insert_char(char)
                self.literal_next = False
            # Handle EOF now as Ctrl+D must be pressed twice
            # consecutively to stop reading from the input.
            elif self.is_eof(char):
                if self.eof_pressed:
                    break
            elif self.handle(char):
                # Dispatched to handler.
                pass
            else:
                # Insert as normal character.
                self.insert_char(char)

            self.eof_pressed = self.is_eof(char)

        return ''.join(self.password)