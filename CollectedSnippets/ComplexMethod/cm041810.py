def feed(self, char: str):
        """Feed a single character into the streamer."""
        # Handle newlines
        if char == "\n":
            self.write_char(char)
            self.line_start = True
            if not self.in_code_block:
                self.active_styles.clear()
            self.potential_marker = ""
            self.list_marker_count = 0  # Reset list state
            return

        # Handle horizontal rules
        if not self.in_code_block and self.handle_horizontal_rule(char):
            return

        # Handle line start features
        if not self.in_code_block and self.handle_line_start(char):
            return

        # Handle markdown markers
        if char in ["*", "`"]:
            if not self.handle_marker(char):
                self.write_char(char)
        else:
            if self.potential_marker:
                self.write_char(self.potential_marker)
            self.potential_marker = ""
            self.write_char(char)