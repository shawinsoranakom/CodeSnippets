def _categorize_pattern(self, pattern: str) -> int:
        """Categorize pattern for specialized handling"""
        if not isinstance(pattern, str):
            return self.PATTERN_TYPES["PATH"]

        # Check if it's a regex pattern
        if pattern.startswith("^") or pattern.endswith("$") or "\\d" in pattern:
            return self.PATTERN_TYPES["REGEX"]

        if pattern.count("*") == 1:
            if pattern.startswith("*."):
                return self.PATTERN_TYPES["SUFFIX"]
            if pattern.endswith("/*"):
                return self.PATTERN_TYPES["PREFIX"]

        if "://" in pattern and pattern.startswith("*."):
            return self.PATTERN_TYPES["DOMAIN"]

        return self.PATTERN_TYPES["PATH"]