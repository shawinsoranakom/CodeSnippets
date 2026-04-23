def regex_search(
        self,
        text: str,
        pattern: str,
        flags: str | None = None,
        return_groups: bool = False,
    ) -> str:
        """Search text using regex pattern.

        Args:
            text: The text to search
            pattern: The regex pattern
            flags: Optional flags string
            return_groups: Whether to return capture groups

        Returns:
            str: JSON array of matches
        """
        if len(text) > self.config.max_text_length:
            raise CommandExecutionError(
                f"Text exceeds maximum length of {self.config.max_text_length}"
            )

        try:
            regex = re.compile(pattern, self._parse_flags(flags))
        except re.error as e:
            raise CommandExecutionError(f"Invalid regex pattern: {e}")

        matches = []
        for match in regex.finditer(text):
            if len(matches) >= self.config.max_matches:
                break

            if return_groups and match.groups():
                matches.append(
                    {
                        "match": match.group(0),
                        "groups": match.groups(),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )
            else:
                matches.append(
                    {
                        "match": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        result = {
            "count": len(matches),
            "matches": matches,
        }

        if len(matches) >= self.config.max_matches:
            result["truncated"] = True

        return json.dumps(result, indent=2)