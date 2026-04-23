def push(self, char: int | bytes) -> None:
        """
        Processes a character by updating the buffer and handling special key mappings.
        """
        assert isinstance(char, (int, bytes))
        ord_char = char if isinstance(char, int) else ord(char)
        char = ord_char.to_bytes()
        self.buf.append(ord_char)

        if char in self.keymap:
            if self.keymap is self.compiled_keymap:
                # sanity check, buffer is empty when a special key comes
                assert len(self.buf) == 1
            k = self.keymap[char]
            trace('found map {k!r}', k=k)
            if isinstance(k, dict):
                self.keymap = k
            else:
                self.insert(Event('key', k, bytes(self.flush_buf())))
                self.keymap = self.compiled_keymap

        elif self.buf and self.buf[0] == 27:  # escape
            # escape sequence not recognized by our keymap: propagate it
            # outside so that i can be recognized as an M-... key (see also
            # the docstring in keymap.py
            trace('unrecognized escape sequence, propagating...')
            self.keymap = self.compiled_keymap
            self.insert(Event('key', '\033', b'\033'))
            for _c in self.flush_buf()[1:]:
                self.push(_c)

        else:
            try:
                decoded = bytes(self.buf).decode(self.encoding)
            except UnicodeError:
                return
            else:
                self.insert(Event('key', decoded, bytes(self.flush_buf())))
            self.keymap = self.compiled_keymap