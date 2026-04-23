async def run(self, input_data: Input, **kwargs) -> BlockOutput:
        # Security fix: Add limits to prevent ReDoS and memory exhaustion
        MAX_TEXT_LENGTH = 1_000_000  # 1MB character limit
        MAX_MATCHES = 1000  # Maximum number of matches to prevent memory exhaustion
        MAX_MATCH_LENGTH = 10_000  # Maximum length per match

        flags = 0
        if not input_data.case_sensitive:
            flags = flags | re.IGNORECASE
        if input_data.dot_all:
            flags = flags | re.DOTALL

        if isinstance(input_data.text, str):
            txt = input_data.text
        else:
            txt = json.dumps(input_data.text)

        # Limit text size to prevent DoS
        if len(txt) > MAX_TEXT_LENGTH:
            txt = txt[:MAX_TEXT_LENGTH]

        # Validate regex pattern to prevent dangerous patterns
        dangerous_patterns = [
            r".*\+.*\+",  # Nested quantifiers
            r".*\*.*\*",  # Nested quantifiers
            r"(?=.*\+)",  # Lookahead with quantifier
            r"(?=.*\*)",  # Lookahead with quantifier
            r"\(.+\)\+",  # Group with nested quantifier
            r"\(.+\)\*",  # Group with nested quantifier
            r"\([^)]+\+\)\+",  # Nested quantifiers like (a+)+
            r"\([^)]+\*\)\*",  # Nested quantifiers like (a*)*
        ]

        # Check if pattern is potentially dangerous
        is_dangerous = any(
            re.search(dangerous, input_data.pattern) for dangerous in dangerous_patterns
        )

        # Use regex module with timeout for dangerous patterns
        # For safe patterns, use standard re module for compatibility
        try:
            matches = []
            match_count = 0

            if is_dangerous:
                # Use regex module with timeout (5 seconds) for dangerous patterns
                # The regex module supports timeout parameter in finditer
                try:
                    for match in regex.finditer(
                        input_data.pattern, txt, flags=flags, timeout=5.0
                    ):
                        if match_count >= MAX_MATCHES:
                            break
                        if input_data.group <= len(match.groups()):
                            match_text = match.group(input_data.group)
                            # Limit match length to prevent memory exhaustion
                            if len(match_text) > MAX_MATCH_LENGTH:
                                match_text = match_text[:MAX_MATCH_LENGTH]
                            matches.append(match_text)
                            match_count += 1
                except regex.error as e:
                    # Timeout occurred or regex error
                    if "timeout" in str(e).lower():
                        # Timeout - return empty results
                        pass
                    else:
                        # Other regex error
                        raise
            else:
                # Use standard re module for non-dangerous patterns
                for match in re.finditer(input_data.pattern, txt, flags):
                    if match_count >= MAX_MATCHES:
                        break
                    if input_data.group <= len(match.groups()):
                        match_text = match.group(input_data.group)
                        # Limit match length to prevent memory exhaustion
                        if len(match_text) > MAX_MATCH_LENGTH:
                            match_text = match_text[:MAX_MATCH_LENGTH]
                        matches.append(match_text)
                        match_count += 1

            if not input_data.find_all:
                matches = matches[:1]

            for match in matches:
                yield "positive", match
            if not matches:
                yield "negative", input_data.text

            yield "matched_results", matches
            yield "matched_count", len(matches)
        except Exception:
            # Return empty results on any regex error
            yield "negative", input_data.text
            yield "matched_results", []
            yield "matched_count", 0