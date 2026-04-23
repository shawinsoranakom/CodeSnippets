def handle_marker(self, char: str) -> bool:
        """Handle markdown markers."""
        self.potential_marker += char

        # Code block
        if char == "`" and not Style.CODE in self.active_styles:
            self.code_fence_count += 1
            if self.code_fence_count == 3:
                self.code_fence_count = 0
                if not self.in_code_block:
                    self.in_code_block = True
                    self.active_styles.add(Style.CODE_BLOCK)
                    sys.stdout.write("\n")
                else:
                    self.in_code_block = False
                    self.active_styles.remove(Style.CODE_BLOCK)
                    sys.stdout.write("\n")
                return True
        else:
            self.code_fence_count = 0

        # Inline code
        if char == "`" and len(self.potential_marker) == 1:
            if Style.CODE in self.active_styles:
                self.active_styles.remove(Style.CODE)
            else:
                self.active_styles.add(Style.CODE)
            self.potential_marker = ""
            return True

        # Bold marker
        if self.potential_marker == "**":
            if Style.BOLD in self.active_styles:
                self.active_styles.remove(Style.BOLD)
            else:
                self.active_styles.add(Style.BOLD)
            self.potential_marker = ""
            return True

        # Italic marker
        elif self.potential_marker == "*" and char != "*":
            if Style.ITALIC in self.active_styles:
                self.active_styles.remove(Style.ITALIC)
            else:
                self.active_styles.add(Style.ITALIC)
            self.write_char(char)
            self.potential_marker = ""
            return True

        # Not a complete marker
        if len(self.potential_marker) > 2:
            self.write_char(self.potential_marker[0])
            self.potential_marker = self.potential_marker[1:]

        return False