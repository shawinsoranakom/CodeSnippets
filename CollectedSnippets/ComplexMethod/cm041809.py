def handle_line_start(self, char: str) -> bool:
        """Handle special characters at start of lines."""
        if not self.line_start:
            return False

        if char == "#":
            self.header_level += 1
            return True
        elif self.header_level > 0:
            if char == " ":
                self.active_styles.add(Style.HEADER)
                return True
            self.header_level = 0

        elif char == "-" and not any(
            s in self.active_styles for s in [Style.BOLD, Style.ITALIC]
        ):
            self.list_marker_count = 1
            return True
        elif self.list_marker_count == 1 and char == " ":
            sys.stdout.write("  • ")  # Write bullet point
            sys.stdout.flush()
            self.list_marker_count = 0
            self.line_start = False
            return True

        self.line_start = False
        return False