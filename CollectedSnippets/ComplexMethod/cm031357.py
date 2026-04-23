def get_prompt(self, lineno: int, cursor_on_line: bool) -> str:
        """Return what should be in the left-hand margin for line
        'lineno'."""
        if self.arg is not None and cursor_on_line:
            prompt = f"(arg: {self.arg}) "
        elif self.paste_mode:
            prompt = "(paste) "
        elif "\n" in self.buffer:
            if lineno == 0:
                prompt = self.ps2
            elif self.ps4 and lineno == self.buffer.count("\n"):
                prompt = self.ps4
            else:
                prompt = self.ps3
        else:
            prompt = self.ps1
        return prompt