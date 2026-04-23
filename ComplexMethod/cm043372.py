def _quick_depth(path: str) -> int:
        """Ultra fast path depth calculation.

        Examples:
            - "http://example.com" -> 0  # No path segments
            - "http://example.com/" -> 0  # Empty path
            - "http://example.com/a" -> 1
            - "http://example.com/a/b" -> 2
        """
        if not path or path == '/':
            return 0

        if '/' not in path:
            return 0

        depth = 0
        last_was_slash = True

        for c in path:
            if c == '/':
                if not last_was_slash:
                    depth += 1
                last_was_slash = True
            else:
                last_was_slash = False

        if not last_was_slash:
            depth += 1

        return depth