def match(self, path_pattern, *, case_sensitive=None):
        """
        Return True if this path matches the given pattern. If the pattern is
        relative, matching is done from the right; otherwise, the entire path
        is matched. The recursive wildcard '**' is *not* supported by this
        method.
        """
        if not hasattr(path_pattern, 'with_segments'):
            path_pattern = self.with_segments(path_pattern)
        if case_sensitive is None:
            case_sensitive = self.parser is posixpath
        path_parts = self.parts[::-1]
        pattern_parts = path_pattern.parts[::-1]
        if not pattern_parts:
            raise ValueError("empty pattern")
        if len(path_parts) < len(pattern_parts):
            return False
        if len(path_parts) > len(pattern_parts) and path_pattern.anchor:
            return False
        globber = _StringGlobber(self.parser.sep, case_sensitive)
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            match = globber.compile(pattern_part)
            if match(path_part) is None:
                return False
        return True