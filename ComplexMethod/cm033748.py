def read(self) -> str:
        """Read and return the next input segment, taking into account parsing boundaries."""
        delimiters = "".join(boundary.delimiters for boundary in self.boundaries)

        if delimiters:
            pattern = '([' + re.escape(delimiters) + '])'
            regex = re.compile(pattern)
            parts = regex.split(self.remainder, 1)
        else:
            parts = [self.remainder]

        if len(parts) > 1:
            value, delimiter, remainder = parts
        else:
            value, delimiter, remainder = parts[0], None, None

        for boundary in reversed(self.boundaries):
            if delimiter and delimiter in boundary.delimiters:
                boundary.match = delimiter
                self.consumed += value + delimiter
                break

            boundary.match = None
            boundary.ready = False

            if boundary.required:
                break

        self.remainder = remainder

        return value