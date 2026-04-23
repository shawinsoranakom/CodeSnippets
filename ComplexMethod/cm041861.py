def line_postprocessor(self, line):
        # If the line count attribute is set and non-zero, decrement and skip the line
        if hasattr(self, "code_line_count") and self.code_line_count > 0:
            self.code_line_count -= 1
            return None

        if re.match(r"^(\s*>>>\s*|\s*\.\.\.\s*|\s*>\s*|\s*\+\s*|\s*)$", line):
            return None
        if "R version" in line:  # Startup message
            return None
        if line.strip().startswith('[1] "') and line.endswith(
            '"'
        ):  # For strings, trim quotation marks
            return line[5:-1].strip()
        if line.strip().startswith(
            "[1]"
        ):  # Normal R output prefix for non-string outputs
            return line[4:].strip()

        return line