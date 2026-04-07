def _num_plurals(self):
        """
        Return the number of plurals for this catalog language, or 2 if no
        plural string is available.
        """
        match = re.search(r"nplurals=\s*(\d+)", self._plural_string or "")
        if match:
            return int(match[1])
        return 2