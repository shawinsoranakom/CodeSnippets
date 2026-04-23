def _add_pattern(self, pattern: str, pattern_type: int):
        """Add pattern to appropriate matcher"""
        if pattern_type == self.PATTERN_TYPES["REGEX"]:
            # For regex patterns, compile directly without glob translation
            if isinstance(pattern, str) and (
                pattern.startswith("^") or pattern.endswith("$") or "\\d" in pattern
            ):
                self._path_patterns.append(re.compile(pattern))
                return
        elif pattern_type == self.PATTERN_TYPES["SUFFIX"]:
            self._simple_suffixes.add(pattern[2:])
        elif pattern_type == self.PATTERN_TYPES["PREFIX"]:
            self._simple_prefixes.add(pattern[:-2])
        elif pattern_type == self.PATTERN_TYPES["DOMAIN"]:
            self._domain_patterns.append(re.compile(pattern.replace("*.", r"[^/]+\.")))
        else:
            if isinstance(pattern, str):
                # Handle complex glob patterns
                if "**" in pattern:
                    pattern = pattern.replace("**", ".*")
                if "{" in pattern:
                    # Convert {a,b} to (a|b)
                    pattern = re.sub(
                        r"\{([^}]+)\}",
                        lambda m: f'({"|".join(m.group(1).split(","))})',
                        pattern,
                    )
                pattern = fnmatch.translate(pattern)
            self._path_patterns.append(
                pattern if isinstance(pattern, Pattern) else re.compile(pattern)
            )